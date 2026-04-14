"""Orchestration pipeline: discovery → verification → decision → write."""

import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from markphotomediaapprovalstatusautolib.constants import (
    COL_FILE,
    COL_PATH,
    COMBINED_HASH_THRESHOLD,
    DEFAULT_CONTRIBUTOR_NAME,
    DEFAULT_HASH_CACHE_PATH,
    DEFAULT_PREVIEW_CACHE_DIR,
    DEFAULT_REPORT_DIR,
    PHASH_THRESHOLD,
    STATUS_APPROVED,
    STATUS_COLUMN_KEYWORD,
)
from markphotomediaapprovalstatusautolib.decision import decide
from markphotomediaapprovalstatusautolib.discovery.registry import get_adapter
from markphotomediaapprovalstatusautolib.models import (
    Candidate,
    DetectionResult,
    Evidence,
    PhotoRecord,
)
from markphotomediaapprovalstatusautolib.report.audit_models import AuditEntry
from markphotomediaapprovalstatusautolib.report.audit_writer import AuditWriter
from markphotomediaapprovalstatusautolib.transport.http_client import HttpClient
from markphotomediaapprovalstatusautolib.verification.evidence_builder import build_evidence
from markphotomediaapprovalstatusautolib.verification.hash_cache import HashCache
from shared.file_operations import ensure_directory, save_csv_with_backup


def build_photo_record(row: dict, bank_name: str) -> Optional[PhotoRecord]:
    """Build a PhotoRecord from a CSV row for *bank_name*.

    :param row: Raw CSV row dictionary.
    :param bank_name: Name of the bank being processed.
    :return: PhotoRecord, or None when essential fields are missing.
    """
    import os

    file_name = row.get(COL_FILE, "").strip()
    path = row.get(COL_PATH, "").strip()
    if not file_name:
        return None
    local_path = path if path else file_name  # Cesta is already the full file path
    status_col = f"{bank_name} {STATUS_COLUMN_KEYWORD}"
    return PhotoRecord(
        file=file_name,
        path=path,
        title=row.get("Název", ""),
        description=row.get("Popis", ""),
        keywords=row.get("Klíčová slova", ""),
        bank_statuses={bank_name: row.get(status_col, "")},
        local_file_path=local_path,
    )


def select_best_evidence(evidences: List[Evidence]) -> Optional[Evidence]:
    """Pick the evidence with the lowest pHash distance that has contributor match.

    Falls back to any evidence with a computed distance if no contributor match
    exists (for logging purposes only — such evidence will yield NOT_FOUND).

    :param evidences: List of Evidence objects from all candidates.
    :return: Best Evidence, or None if the list is empty.
    """
    if not evidences:
        return None
    matched = [e for e in evidences if e.contributor_match and e.phash_distance is not None]
    if matched:
        return min(matched, key=lambda e: e.phash_distance)  # type: ignore[arg-type]
    with_distance = [e for e in evidences if e.phash_distance is not None]
    if with_distance:
        return min(with_distance, key=lambda e: e.phash_distance)  # type: ignore[arg-type]
    return evidences[0]


def _build_file_index(all_data: List[dict]) -> Dict[str, int]:
    """Build a mapping from filename to row index in *all_data*.

    Logs a warning when duplicate filenames are detected.

    :param all_data: Complete CSV data.
    :return: Dict mapping filename → last row index.
    """
    index: Dict[str, int] = {}
    for i, row in enumerate(all_data):
        name = row.get(COL_FILE, "")
        if name in index:
            logging.warning("Duplicate filename in CSV: %s (rows %d and %d)", name, index[name], i)
        index[name] = i
    return index


def run_detection(
    all_data: List[dict],
    filtered_data: List[dict],
    csv_path: str,
    banks: List[str],
    contributor_name: str = DEFAULT_CONTRIBUTOR_NAME,
    dry_run: bool = False,
    report_dir: str = DEFAULT_REPORT_DIR,
    headless: bool = True,
    hash_cache_path: str = DEFAULT_HASH_CACHE_PATH,
    preview_cache_dir: str = DEFAULT_PREVIEW_CACHE_DIR,
    phash_threshold: int = PHASH_THRESHOLD,
) -> List[DetectionResult]:
    """Run the full detection pipeline, bank by bank, record by record.

    Outer loop iterates banks; inner loop iterates records for each bank.
    Each bank produces its own audit CSV.  The PhotoMedia CSV is saved once
    per bank (only when FOUND results exist and *dry_run* is False).

    :param all_data: Complete CSV data (used for writing results back).
    :param filtered_data: Records already filtered for the correct status.
    :param csv_path: Path to PhotoMedia.csv.
    :param banks: Canonical bank names to process.
    :param contributor_name: Your contributor username for identity matching.
    :param dry_run: When True, skip writing FOUND results back to the CSV.
    :param report_dir: Directory where per-bank audit CSVs are written.
    :param headless: Run browser headless when True.
    :param hash_cache_path: Path to the SQLite hash cache file.
    :param preview_cache_dir: Directory for caching downloaded preview images.
    :param phash_threshold: Maximum pHash Hamming distance accepted as FOUND.
    :return: List of DetectionResult objects (one per record × bank pair).
    :raises SystemExit: When contributor_name is empty.
    """
    if not contributor_name.strip():
        logging.error("contributor_name is empty — pass --contributor-name to avoid silent mismatches")
        sys.exit(1)

    ensure_directory(report_dir)
    file_to_index = _build_file_index(all_data)
    hash_cache = HashCache(hash_cache_path)
    results: List[DetectionResult] = []
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    with HttpClient() as http_client:
        for bank_name in banks:
            adapter = get_adapter(bank_name)
            if adapter is None:
                logging.warning("No adapter registered for bank: %s", bank_name)
                continue

            # Build portfolio index once per bank for adapters that require it (e.g. Pond5).
            portfolio_index: Optional[List[Tuple[int, str]]] = None
            if bank_name == "Pond5":
                from markphotomediaapprovalstatusautolib.discovery.banks.pond5 import (
                    build_search_vocabulary,
                    crawl_pond5_portfolio,
                    extract_contributor_name,
                )
                from shared.file_operations import load_json_file
                _portfolios_json = os.path.join(
                    os.path.dirname(__file__), "..", "..", "markphotomediaapprovalstatus", "public_portfolios.json"
                )
                _profile_dir = os.path.join(os.path.dirname(__file__), "..", "cookies", "profile_Pond5")
                try:
                    _portfolios = load_json_file(_portfolios_json)
                    _portfolio_url = _portfolios["banks"]["Pond5"]["portfolio_url"]
                    from markphotomediaapprovalstatusautolib.constants import DEFAULT_POND5_PORTFOLIO_CACHE_PATH
                    _search_vocabulary = build_search_vocabulary(filtered_data)
                    portfolio_index = crawl_pond5_portfolio(
                        _portfolio_url,
                        headless=headless,
                        profile_dir=_profile_dir,
                        cache_path=DEFAULT_POND5_PORTFOLIO_CACHE_PATH,
                        search_vocabulary=_search_vocabulary,
                    )
                    logging.info("Pond5 portfolio index: %d assets", len(portfolio_index))
                except Exception as exc:
                    logging.error("Failed to crawl Pond5 portfolio: %s", exc)
                    portfolio_index = []

            audit_path = f"{report_dir}/audit_{bank_name}_{ts}.csv"
            audit_writer = AuditWriter(audit_path)
            bank_found: Dict[str, str] = {}  # file_name → status_col, collected for end-of-bank save

            for row in filtered_data:
                record = build_photo_record(row, bank_name)
                if record is None:
                    continue

                try:
                    candidates: List[Candidate] = adapter.discover(
                        record,
                        http_client=http_client,
                        headless=headless,
                        contributor_name=contributor_name,
                        portfolio_index=portfolio_index,
                    )
                except Exception as exc:
                    logging.error("Discovery error for %s / %s: %s", record.file, bank_name, exc)
                    candidates = []

                evidences: List[Evidence] = []
                for candidate in candidates:
                    ev = build_evidence(
                        local_file_path=record.local_file_path,
                        contributor_name=contributor_name,
                        candidate=candidate,
                        http_client=http_client,
                        hash_cache=hash_cache,
                        preview_cache_dir=preview_cache_dir,
                    )
                    evidences.append(ev)

                best = select_best_evidence(evidences)
                if bank_name == "Pond5" and evidences and (best is None or (best.phash_distance or 999) > phash_threshold):
                    # Stage 2: phash alone failed — re-select by minimum combined phash+dhash distance
                    combined_best = min(
                        evidences,
                        key=lambda e: (e.phash_distance or 999) + (e.dhash_distance or 999),
                    )
                    best = combined_best
                    outcome, reason = decide(best, phash_threshold=phash_threshold, combined_threshold=COMBINED_HASH_THRESHOLD)
                else:
                    outcome, reason = decide(best, phash_threshold=phash_threshold)
                now = datetime.now().isoformat()

                result = DetectionResult(
                    record_file=record.file,
                    bank=bank_name,
                    outcome=outcome,
                    matched_url=best.candidate.url if best and outcome == "FOUND" else None,
                    matched_id=best.candidate.asset_id if best and outcome == "FOUND" else None,
                    evidence=best,
                    reason=reason,
                    timestamp=now,
                )
                results.append(result)

                audit_writer.write(
                    AuditEntry(
                        timestamp=now,
                        local_file=record.file,
                        bank=bank_name,
                        result=outcome,
                        candidate_url=result.matched_url,
                        candidate_id=result.matched_id,
                        contributor_match=best.contributor_match if best else None,
                        phash_distance=best.phash_distance if best else None,
                        dhash_distance=best.dhash_distance if best else None,
                        dimension_match=best.dimension_match if best else None,
                        preview_url=best.candidate.preview_url if best else None,
                        reason=reason,
                    )
                )

                if outcome == "FOUND":
                    logging.info("FOUND: %s on %s → %s", record.file, bank_name, result.matched_url)
                    status_col = f"{bank_name} {STATUS_COLUMN_KEYWORD}"
                    bank_found[record.file] = status_col
                else:
                    logging.debug("NOT_FOUND: %s on %s (%s)", record.file, bank_name, reason)

            if bank_found and not dry_run:
                for file_name, status_col in bank_found.items():
                    idx = file_to_index.get(file_name)
                    if idx is not None:
                        all_data[idx][status_col] = STATUS_APPROVED
                save_csv_with_backup(all_data, csv_path)
                logging.info("Saved %d FOUND updates for %s", len(bank_found), bank_name)

            logging.info(
                "Bank %s complete. FOUND: %d / %d records. Audit: %s",
                bank_name,
                len(bank_found),
                len(filtered_data),
                audit_path,
            )

    logging.info("Detection pipeline complete. %d total results.", len(results))
    return results
