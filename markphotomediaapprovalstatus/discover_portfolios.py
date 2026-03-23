"""One-time discovery script for finding contributor portfolio URLs on photobanks.

Run this script locally to automatically discover your portfolio URLs.
Results are written to public_portfolios.json and can be copied to constants.

Usage:
    python discover_portfolios.py [--csv_path PATH] [--headless] [--banks BANK1,BANK2,...]

Requirements:
    pip install playwright
    playwright install chromium
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).parent))

from markphotomediaapprovalstatuslib.constants import DEFAULT_PHOTO_CSV_PATH, STATUS_COLUMN_KEYWORD
from markphotomediaapprovalstatuslib.public_portfolio.browser import browser_context
from markphotomediaapprovalstatuslib.public_portfolio.constants import DEFAULT_PORTFOLIO_URLS
from markphotomediaapprovalstatuslib.public_portfolio.utils import (
    extract_from_json_ld,
    extract_meta_content,
    extract_title,
)
from markphotomediaapprovalstatuslib.public_portfolio.matching import normalize_text

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

STATUS_APPROVED = "schváleno"

PORTFOLIO_LINK_PATTERNS: Dict[str, str] = {
    "ShutterStock": r'https?://(?:www\.)?shutterstock\.com/g/[^"\'\s>]+',
    "AdobeStock": r'https?://stock\.adobe\.com/(?:[a-z]{2}/)?contributor/\d+/[^"\'\s>?]+',
    "Dreamstime": r'https?://(?:www\.)?dreamstime\.com/[a-zA-Z0-9_-]+_info',
    "DepositPhotos": r'https?://(?:www\.)?depositphotos\.com/portfolio-\d+\.html',
    "123RF": r'https?://(?:www\.)?123rf\.com/profile_[^"\'\s>]+',
    "Pond5": r'https?://(?:www\.)?pond5\.com/artist/[^"\'\s>]+',
    "GettyImages": r'https?://(?:www\.)?gettyimages\.com/search/photographer\?[^"\'\s>]*photographer=[^"\'\s>]+',
    "Alamy": r'https?://(?:www\.)?alamy\.com/portfolio/[^"\'\s>]+\.html',
    "Pixta": r'https?://(?:www\.)?pixtastock\.com/@[^"\'\s>]+',
    "Freepik": r'https?://(?:www\.)?freepik\.com/author/[^"\'\s>]+',
    "BigStockPhoto": r'https?://(?:www\.)?bigstockphoto\.com/search/\?[^"\'\s>]*contributor=[^&"\'\s>]+',
    "Vecteezy": r'https?://(?:www\.)?vecteezy\.com/(?:members|contributors)/[^"\'\s>]+',
    "StoryBlocks": r'https?://(?:www\.)?storyblocks\.com/portfolio/[^"\'\s>]+',
    "Envato": r'https?://elements\.envato\.com/user/[^"\'\s>]+',
    "500px": r'https?://500px\.com/p/[^"\'\s>]+',
    "MostPhotos": r'https?://(?:www\.)?mostphotos\.com/photographer/[^"\'\s>]+',
}

SEARCH_URL_TEMPLATES: Dict[str, str] = {
    "ShutterStock": "https://www.shutterstock.com/search/{query}",
    "AdobeStock": "https://stock.adobe.com/search?k={query}",
    "Dreamstime": "https://www.dreamstime.com/search.php?srh_field={query}",
    "DepositPhotos": "https://depositphotos.com/photos/{query}.html",
    "123RF": "https://www.123rf.com/stock-photo/{query}.html",
    "Pond5": "https://www.pond5.com/search?kw={query}&media=photos",
    "GettyImages": "https://www.gettyimages.com/photos/{query}",
    "Alamy": "https://www.alamy.com/stock-photo/{query}.html",
    "Pixta": "https://www.pixtastock.com/search?keyword={query}",
    "Freepik": "https://www.freepik.com/search?format=search&query={query}",
    "BigStockPhoto": "https://www.bigstockphoto.com/search/?search_word={query}",
    "Vecteezy": "https://www.vecteezy.com/search?q={query}",
    "StoryBlocks": "https://www.storyblocks.com/video/search/{query}",
    "Envato": "https://elements.envato.com/search/{query}",
    "500px": "https://500px.com/search?q={query}",
    "MostPhotos": "https://www.mostphotos.com/search?phrase={query}",
}

ITEM_URL_PATTERNS: Dict[str, str] = {
    "ShutterStock": r'https?://(?:www\.)?shutterstock\.com/image-(?:photo|illustration|vector)/[^"\'\s>]+-\d+',
    "AdobeStock": r'https?://stock\.adobe\.com/(?:[a-z]{2}/)?(?:images|stock-photo)/[^"\'\s>]+/\d+',
    "Dreamstime": r'https?://(?:www\.)?dreamstime\.com/[^"\'\s>]*-image\d+',
    "DepositPhotos": r'https?://(?:www\.)?depositphotos\.com/(?:photo|vector)/[^"\'\s>]+-\d+\.html',
    "123RF": r'https?://(?:www\.)?123rf\.com/(?:photo|vector|illustration)_\d+[^"\'\s>]*\.html',
    "Pond5": r'https?://(?:www\.)?pond5\.com/(?:stock-photo|stock-footage|stock-video|stock-music)/item/\d+',
    "GettyImages": r'https?://(?:www\.)?gettyimages\.com/detail/(?:photo|illustration|video)/[^"\'\s>]+-\d+',
    "Alamy": r'https?://(?:www\.)?alamy\.com/(?:stock-photo-|image-details/)[^"\'\s>]+\.html',
    "Pixta": r'https?://(?:www\.)?pixtastock\.com/(?:photo|illustration|video)/\d+',
    "Freepik": r'https?://(?:www\.)?freepik\.com/(?:free-photo|free-vector|premium-photo|premium-vector)/[^"\'\s>]+',
    "BigStockPhoto": r'https?://(?:www\.)?bigstockphoto\.com/image-\d+[^"\'\s>]*',
    "Vecteezy": r'https?://(?:www\.)?vecteezy\.com/(?:photo|vector|video|illustration)/\d+[^"\'\s>]*',
    "StoryBlocks": r'https?://(?:www\.)?storyblocks\.com/(?:video|audio|image|stock-item)/[^"\'\s>]+',
    "Envato": r'https?://elements\.envato\.com/[^"\'\s>]+-[A-Z0-9]{6,}',
    "500px": r'https?://500px\.com/photo/\d+[^"\'\s>]*',
    "MostPhotos": r'https?://(?:www\.)?mostphotos\.com/\d+/[^"\'\s>]+',
}

UNSUPPORTED_BANKS = {"CanStockPhoto"}

MAX_SEARCH_RESULTS = 10
MAX_DISCOVERY_ATTEMPTS = 3


def load_csv(csv_path: str) -> List[dict]:
    """Load PhotoMedia.csv."""
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def get_approved_records(data: List[dict], bank: str) -> List[dict]:
    """Get records with status 'schváleno' for a given bank."""
    status_col = f"{bank} {STATUS_COLUMN_KEYWORD}"
    results = []
    for row in data:
        if row.get(status_col, "").strip().lower() == STATUS_APPROVED:
            title = row.get("Název", "").strip()
            if title:
                results.append(row)
    return results


def build_query(title: str) -> str:
    """Build search query from title (first 8 words)."""
    words = title.split()[:8]
    return quote_plus(" ".join(words))


def fetch_html(context, url: str, wait_ms: int = 5000) -> str:
    """Fetch page HTML using Playwright."""
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(wait_ms)
        return page.content()
    except Exception as exc:
        logging.warning("Failed to fetch %s: %s", url, exc)
        return ""
    finally:
        page.close()


def extract_title_from_html(html: str) -> str:
    """Extract title from HTML page."""
    data = extract_from_json_ld(html)
    return data.get("title") or extract_meta_content(html, "og:title") or extract_title(html) or ""


def extract_description_from_html(html: str) -> str:
    """Extract description from HTML page."""
    data = extract_from_json_ld(html)
    return data.get("description") or extract_meta_content(html, "og:description") or ""


def find_portfolio_link(html: str, bank: str) -> Optional[str]:
    """Find contributor portfolio link in HTML using bank-specific pattern."""
    pattern = PORTFOLIO_LINK_PATTERNS.get(bank)
    if not pattern:
        return None
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(0)
    return None


def discover_portfolio_for_bank(
    context, bank: str, approved_records: List[dict]
) -> Tuple[Optional[str], Optional[str]]:
    """Discover portfolio URL for a bank by searching for approved photos.

    :param context: Playwright browser context.
    :param bank: Bank name.
    :param approved_records: Records with 'schváleno' status for this bank.
    :return: Tuple of (portfolio_url, contributor_name).
    """
    search_template = SEARCH_URL_TEMPLATES.get(bank)
    item_pattern = ITEM_URL_PATTERNS.get(bank)

    if not search_template or not item_pattern:
        logging.warning("%s: no search template or item pattern defined", bank)
        return None, None

    attempts = 0
    for record in approved_records:
        if attempts >= MAX_DISCOVERY_ATTEMPTS:
            break

        title = record.get("Název", "").strip()
        if not title:
            continue

        query = build_query(title)
        search_url = search_template.format(query=query)
        attempts += 1

        logging.info("%s: searching for '%s'", bank, title[:60])
        logging.info("  URL: %s", search_url)

        search_html = fetch_html(context, search_url)
        if not search_html:
            continue

        item_links = re.findall(item_pattern, search_html, re.IGNORECASE)
        unique_links = list(dict.fromkeys(item_links))

        if not unique_links:
            logging.info("  No item links found in search results")
            continue

        logging.info("  Found %d item links, checking first %d", len(unique_links), min(MAX_SEARCH_RESULTS, len(unique_links)))

        for link in unique_links[:MAX_SEARCH_RESULTS]:
            time.sleep(1)
            detail_html = fetch_html(context, link)
            if not detail_html:
                continue

            page_title = extract_title_from_html(detail_html)
            page_desc = extract_description_from_html(detail_html)

            if normalize_text(title) in normalize_text(page_title) or normalize_text(page_title) in normalize_text(title):
                logging.info("  MATCH found at: %s", link)
                portfolio_url = find_portfolio_link(detail_html, bank)
                contributor = extract_from_json_ld(detail_html).get("author", "")
                if portfolio_url:
                    logging.info("  Portfolio URL: %s", portfolio_url)
                    logging.info("  Contributor: %s", contributor)
                    return portfolio_url, contributor
                else:
                    logging.info("  Title matched but no portfolio link found on detail page")
                    logging.info("  Contributor from JSON-LD: %s", contributor)
                    return None, contributor

    return None, None


def main() -> None:
    """Run portfolio discovery for all supported banks."""
    parser = argparse.ArgumentParser(description="Discover contributor portfolio URLs on photobanks")
    parser.add_argument("--csv_path", default=DEFAULT_PHOTO_CSV_PATH, help="Path to PhotoMedia.csv")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--banks", help="Comma-separated list of banks to check (default: all)")
    parser.add_argument("--output", default="discovered_portfolios.json", help="Output JSON file")
    args = parser.parse_args()

    logging.info("Loading CSV from: %s", args.csv_path)
    data = load_csv(args.csv_path)
    logging.info("Loaded %d records", len(data))

    banks_to_check = list(SEARCH_URL_TEMPLATES.keys())
    if args.banks:
        banks_to_check = [b.strip() for b in args.banks.split(",")]

    results: Dict[str, dict] = {}

    with browser_context(headless=args.headless) as context:
        for bank in banks_to_check:
            if bank in UNSUPPORTED_BANKS:
                logging.info("%s: SKIPPED (unsupported/closed)", bank)
                continue

            approved = get_approved_records(data, bank)
            if not approved:
                logging.info("%s: no approved records found, skipping", bank)
                continue

            logging.info("=" * 60)
            logging.info("%s: %d approved records available for discovery", bank, len(approved))
            logging.info("=" * 60)

            portfolio_url, contributor = discover_portfolio_for_bank(context, bank, approved)

            if portfolio_url:
                results[bank] = {"portfolio_url": portfolio_url, "contributor": contributor}
                logging.info("%s: SUCCESS - %s", bank, portfolio_url)
            elif contributor:
                results[bank] = {"portfolio_url": None, "contributor": contributor}
                logging.info("%s: contributor found (%s) but no portfolio URL", bank, contributor)
            else:
                logging.info("%s: FAILED - could not discover portfolio", bank)

            time.sleep(2)

    logging.info("")
    logging.info("=" * 60)
    logging.info("DISCOVERY RESULTS")
    logging.info("=" * 60)

    if results:
        for bank, info in results.items():
            url = info.get("portfolio_url", "N/A")
            contributor = info.get("contributor", "N/A")
            logging.info("  %s: %s (contributor: %s)", bank, url, contributor)

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logging.info("")
        logging.info("Results saved to: %s", args.output)
        logging.info("")
        logging.info("Copy the portfolio URLs to:")
        logging.info("  markphotomediaapprovalstatuslib/public_portfolio/constants.py")
        logging.info("  -> DEFAULT_PORTFOLIO_URLS dict")
    else:
        logging.info("  No portfolios discovered.")

    undiscovered = [b for b in banks_to_check if b not in results and b not in UNSUPPORTED_BANKS]
    if undiscovered:
        logging.info("")
        logging.info("Banks without results: %s", ", ".join(undiscovered))


if __name__ == "__main__":
    main()