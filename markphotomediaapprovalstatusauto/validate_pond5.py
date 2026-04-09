"""Pond5 detection validator.

Validates the detection algorithm against photos already marked as 'schvaleno'
in PhotoMedia.csv.  The validator feeds approved records through the SAME detection
code used by markphotomediaapprovalstatusauto — it only differs in which records it
feeds in and how it interprets the results.

Detection code imported (not duplicated):
    pipeline.build_photo_record()    — CSV row → PhotoRecord
    decision.decide()               — FOUND / NOT_FOUND verdict
    pond5.crawl_pond5_portfolio()   — portfolio crawl (same as main run)
    image_hasher.*                  — generate_phash, generate_dhash, hamming_distance
    preview_downloader.*            — download_preview (with disk cache)
    hash_cache.HashCache            — local file hash cache

Performance strategy — download once, compare offline:
    Phase 1: Download all portfolio previews and compute pHash/dHash for each asset.
             Each preview is downloaded exactly once per run (disk-cached by download_preview).
    Phase 2: For each CSV record, compute local pHash (from HashCache), then find the
             best-matching portfolio asset by Hamming distance using the in-memory dict.
             Only one Evidence object is built per record — no repeated downloads.

The validator produces THREE output files.  Two should be empty on a healthy run:
  - validate_Pond5_matched.txt        (File 1 — records found on web, ~95%+)
  - validate_Pond5_csv_not_on_web.txt (File 2 — approved in CSV but missing on web, should be EMPTY)
  - validate_Pond5_web_not_in_csv.txt (File 3 — web asset not in CSV, should be EMPTY)

Non-empty File 2 means the user likely marked a photo as approved when it was not.
Non-empty File 3 means a photo was approved on the bank without being recorded in PhotoMedia.csv.

Usage:
    python save_bank_session.py --bank Pond5   # one-time session setup
    python validate_pond5.py --visible
    python validate_pond5.py --sample 50 --visible
"""

import argparse
import logging
import os
import sys
from typing import Dict, List

import tqdm

from shared.file_operations import ensure_directory, load_csv, load_json_file
from shared.logging_config import setup_logging
from shared.utils import get_log_filename

from markphotomediaapprovalstatusautolib.constants import (
    COMBINED_HASH_THRESHOLD,
    DEFAULT_HASH_CACHE_PATH,
    DEFAULT_LOG_DIR,
    DEFAULT_PHOTO_CSV_PATH,
    DEFAULT_POND5_PORTFOLIO_CACHE_PATH,
    DEFAULT_PREVIEW_CACHE_DIR,
    PHASH_THRESHOLD,
    STATUS_APPROVED,
)
from markphotomediaapprovalstatusautolib.decision import decide
from markphotomediaapprovalstatusautolib.discovery.banks.pond5 import (
    build_search_vocabulary,
    crawl_pond5_portfolio,
    extract_contributor_name,
)
from markphotomediaapprovalstatusautolib.models import Candidate, Evidence
from markphotomediaapprovalstatusautolib.pipeline import build_photo_record
from markphotomediaapprovalstatusautolib.status_handler import filter_records_by_bank_status
from markphotomediaapprovalstatusautolib.transport.http_client import HttpClient
from markphotomediaapprovalstatusautolib.verification.evidence_builder import (
    build_portfolio_phash_index,
    find_best_combined_match,
    find_best_portfolio_match,
)
from markphotomediaapprovalstatusautolib.verification.hash_cache import HashCache
from markphotomediaapprovalstatusautolib.verification.image_hasher import hamming_distance

_PORTFOLIOS_JSON = os.path.join(
    os.path.dirname(__file__), "..", "markphotomediaapprovalstatus", "public_portfolios.json"
)
_PROFILE_DIR = os.path.join(os.path.dirname(__file__), "cookies", "profile_Pond5")

_MATCH_THRESHOLD_PCT = 100.0


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments.

    :return: Parsed namespace.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Validate Pond5 detection algorithm against approved photos. "
            "Produces 3 output files: matched (should be ~95%+), "
            "csv-not-on-web (should be empty), web-not-in-csv (should be empty)."
        )
    )
    parser.add_argument("--csv-path", type=str, default=DEFAULT_PHOTO_CSV_PATH)
    parser.add_argument("--sample", type=int, default=0, help="Limit to first N approved records (0=all)")
    parser.add_argument("--phash-threshold", type=int, default=PHASH_THRESHOLD)
    parser.add_argument("--preview-cache-dir", type=str, default=DEFAULT_PREVIEW_CACHE_DIR)
    parser.add_argument("--hash-cache", type=str, default=DEFAULT_HASH_CACHE_PATH)
    parser.add_argument("--log-dir", type=str, default=DEFAULT_LOG_DIR)
    parser.add_argument("--output-dir", type=str, default=".", help="Directory for the 3 report files")
    parser.add_argument("--visible", action="store_true", help="Show browser window during crawl")
    parser.add_argument("--portfolio-cache", type=str, default=DEFAULT_POND5_PORTFOLIO_CACHE_PATH, help="Path to the portfolio CSV cache file")
    parser.add_argument("--datadome-cooldown", type=int, default=60, help="Seconds to wait after DataDome block before recovery (default: 60)")
    parser.add_argument("--captcha-timeout", type=int, default=300, help="Seconds to wait in visible browser for CAPTCHA solving (default: 300)")
    parser.add_argument("--cache-only", action="store_true", help="Skip portfolio crawl and use only the existing portfolio cache file")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()



def _write_file(path: str, lines: list) -> None:
    """Write *lines* to *path*.

    :param path: Destination file path.
    :param lines: Content lines.
    """
    ensure_directory(os.path.dirname(os.path.abspath(path)))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + ("\n" if lines else ""))




def main() -> None:
    """Run the Pond5 validation pipeline."""
    args = parse_arguments()
    ensure_directory(args.log_dir)
    setup_logging(debug=args.debug, log_file=get_log_filename(args.log_dir))
    logging.info("=== Pond5 Validator ===")

    out_matched = os.path.join(args.output_dir, "validate_Pond5_matched.txt")
    out_csv_not_web = os.path.join(args.output_dir, "validate_Pond5_csv_not_on_web.txt")
    out_web_not_csv = os.path.join(args.output_dir, "validate_Pond5_web_not_in_csv.txt")

    # 1. Load portfolio URL
    try:
        portfolios = load_json_file(_PORTFOLIOS_JSON)
        portfolio_url = portfolios["banks"]["Pond5"]["portfolio_url"]
    except Exception as exc:
        logging.error("Cannot load Pond5 portfolio URL: %s", exc)
        sys.exit(1)

    contributor_name = extract_contributor_name(portfolio_url)
    logging.info("Portfolio URL: %s (contributor: %s)", portfolio_url, contributor_name)

    # 2. Load CSV — validators check ALL approved records, no edit-type filtering
    try:
        all_data = load_csv(args.csv_path)
    except Exception as exc:
        logging.error("Failed to load CSV: %s", exc)
        sys.exit(1)

    approved = filter_records_by_bank_status(all_data, "Pond5", STATUS_APPROVED)
    if not approved:
        logging.info("No 'schvaleno' Pond5 records — nothing to validate.")
        return

    if args.sample > 0:
        approved = approved[: args.sample]

    csv_count = len(approved)
    logging.info("CSV approved records (Pond5 / sample): %d", csv_count)

    hash_cache = HashCache(args.hash_cache)

    with HttpClient() as http_client:
        # 3. Load portfolio — from cache only or with fresh crawl
        if args.cache_only:
            from markphotomediaapprovalstatusautolib.discovery.banks.pond5 import PortfolioCache
            full_portfolio = PortfolioCache(args.portfolio_cache).load()
            if not full_portfolio:
                logging.error("Portfolio cache is empty. Run without --cache-only to crawl first.")
                sys.exit(1)
            logging.info("Cache-only mode: loaded %d assets from %s", len(full_portfolio), args.portfolio_cache)
        else:
            search_vocabulary = build_search_vocabulary(approved)
            logging.info("Search vocabulary: %d unique substrings from %d approved records", len(search_vocabulary), csv_count)
            full_portfolio = crawl_pond5_portfolio(
                portfolio_url=portfolio_url,
                headless=not args.visible,
                profile_dir=_PROFILE_DIR,
                cache_path=args.portfolio_cache,
                datadome_cooldown=args.datadome_cooldown,
                captcha_timeout=args.captcha_timeout,
                search_vocabulary=search_vocabulary,
            )
            if not full_portfolio:
                logging.error("Portfolio crawl returned 0 assets. Run: python save_bank_session.py --bank Pond5")
                sys.exit(1)

        portfolio_count = len(full_portfolio)
        logging.info(
            "Count comparison -- Portfolio: %d | CSV schvaleno: %d | Diff: %+d",
            portfolio_count, csv_count, portfolio_count - csv_count,
        )

        # 4. Build pHash index for all portfolio assets
        portfolio_phash_index = build_portfolio_phash_index(
            tqdm.tqdm(full_portfolio, desc="Hashing portfolio", unit="asset", ncols=80),
            http_client, args.preview_cache_dir,
        )

        # Build lookup: asset_id → cdn_url (for building Candidate objects later)
        cdn_url_by_id: Dict[int, str] = {asset_id: cdn_url for asset_id, cdn_url in full_portfolio}

        # 9. Final match: all CSV records against combined index
        logging.info("Final matching: %d CSV records against %d portfolio assets...", csv_count, portfolio_count)
        matched_lines: List[str] = []
        csv_not_web_lines: List[str] = []
        matched_asset_ids: set = set()

        for row in tqdm.tqdm(approved, desc="Final matching", unit="record", ncols=80):
            record = build_photo_record(row, "Pond5")
            if record is None:
                continue

            if not os.path.exists(record.local_file_path):
                logging.warning("Local file does not exist, skipping: %s", record.local_file_path)
                continue

            local_hashes = hash_cache.get_or_compute(record.local_file_path)
            if local_hashes is None:
                logging.warning("Cannot hash local file %s — skipping", record.local_file_path)
                continue

            local_phash, local_dhash = local_hashes

            if not portfolio_phash_index:
                csv_not_web_lines.append(f"{record.file} [portfolio index empty]")
                continue

            # Stage 1: phash-only match (fast path — same as main pipeline)
            best_id, best_phash_dist = find_best_portfolio_match(local_phash, portfolio_phash_index)
            if best_id is None:
                csv_not_web_lines.append(f"{record.file} [no candidates]")
                continue
            best_dhash_dist = hamming_distance(local_dhash, portfolio_phash_index[best_id][1])
            use_combined = False

            if best_phash_dist > args.phash_threshold:
                # Stage 2: combined phash+dhash match — fallback for image variants
                # (sharpen/BW/negative whose pHash may be misleading vs CDN thumbnails)
                comb_id, comb_pd, comb_dd = find_best_combined_match(
                    local_phash, local_dhash, portfolio_phash_index
                )
                if comb_id is not None:
                    best_id, best_phash_dist, best_dhash_dist = comb_id, comb_pd, comb_dd
                    use_combined = True

            # Build Evidence and call decide()
            candidate = Candidate(
                bank="Pond5",
                url=f"https://www.pond5.com/stock-footage/{best_id}/",
                preview_url=cdn_url_by_id[best_id],
                contributor_name=contributor_name,
                asset_id=str(best_id),
            )
            evidence = Evidence(
                candidate=candidate,
                phash_distance=best_phash_dist,
                dhash_distance=best_dhash_dist,
                contributor_match=True,
            )
            outcome, reason = decide(
                evidence,
                phash_threshold=args.phash_threshold,
                combined_threshold=COMBINED_HASH_THRESHOLD if use_combined else None,
            )

            if outcome == "FOUND":
                matched_asset_ids.add(str(best_id))
                matched_lines.append(
                    f"{record.file}|asset_{best_id}|phash={best_phash_dist}|{reason}|{candidate.preview_url}"
                )
                logging.debug("MATCHED: %s -> asset_%s (phash=%d, %s)", record.file, best_id, best_phash_dist, reason)
            else:
                best_url = cdn_url_by_id.get(best_id, "") if best_id else ""
                csv_not_web_lines.append(
                    f"{record.file} [best_phash={best_phash_dist}, {reason}]|best_asset={best_id}|{best_url}"
                )
                logging.info("CSV_NOT_ON_WEB: %s (best_phash=%d, %s)", record.file, best_phash_dist, reason)

    # 10. Reverse pass: portfolio assets not claimed by any CSV record
    web_not_csv_lines: List[str] = []
    for asset_id, cdn_url in full_portfolio:
        if str(asset_id) not in matched_asset_ids:
            web_not_csv_lines.append(f"asset_{asset_id}|{cdn_url}")
            logging.info("WEB_NOT_IN_CSV: asset_%d | %s", asset_id, cdn_url)

    # 7. Write 3 report files
    _write_file(out_matched, matched_lines)
    _write_file(out_csv_not_web, csv_not_web_lines)
    _write_file(out_web_not_csv, web_not_csv_lines)

    matched_count = len(matched_lines)
    pct = (matched_count / csv_count * 100) if csv_count else 0.0

    print()
    print("=" * 60)
    print("  Pond5 Validation Results")
    print("=" * 60)
    print(f"  Portfolio assets crawled       : {portfolio_count}")
    print(f"  CSV 'schvaleno' records        : {csv_count}")
    print(f"  Matched (phash <= {args.phash_threshold})           : {matched_count} / {csv_count}  ({pct:.1f}%)")
    print(f"  CSV approved not found on web  : {len(csv_not_web_lines)}  [File 2 -- should be empty]")
    print(f"  Web assets not in CSV          : {len(web_not_csv_lines)}  [File 3 -- should be empty]")
    print("=" * 60)
    print(f"  File 1 (matched)     : {out_matched}")
    print(f"  File 2 (csv missing) : {out_csv_not_web}")
    print(f"  File 3 (web extra)   : {out_web_not_csv}")
    print("=" * 60)

    if pct < _MATCH_THRESHOLD_PCT:
        print()
        print(f"  *** WARNING: match rate {pct:.1f}% is below 95% threshold ***")
        print("  Likely causes: bank changed HTML/CDN structure, or pHash threshold too strict.")

    if csv_not_web_lines:
        print()
        print(f"  *** DATA QUALITY ISSUE: {len(csv_not_web_lines)} records marked 'schvaleno'")
        print("      in PhotoMedia.csv but NOT found in the Pond5 portfolio. ***")
        print()
        print("  These records were most likely INCORRECTLY marked as approved.")
        print("  Please review File 2 and correct the status in PhotoMedia.csv.")

    if web_not_csv_lines:
        print()
        print(f"  *** DATA QUALITY ISSUE: {len(web_not_csv_lines)} Pond5 portfolio assets")
        print("      have NO matching 'schvaleno' record in PhotoMedia.csv. ***")
        print()
        print("  Photos approved on Pond5 but not recorded in your database.")
        print("  Please review File 3 and update PhotoMedia.csv accordingly.")


if __name__ == "__main__":
    main()
