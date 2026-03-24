"""Runner for public portfolio approval detection."""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from markphotomediaapprovalstatuslib.constants import STATUS_APPROVED, STATUS_CHECKED, STATUS_COLUMN_KEYWORD
from markphotomediaapprovalstatuslib.public_portfolio.browser import browser_context
from markphotomediaapprovalstatuslib.public_portfolio.config_store import load_config
from markphotomediaapprovalstatuslib.public_portfolio.constants import DEFAULT_PUBLIC_PORTFOLIO_CONFIG, DEFAULT_PORTFOLIO_URLS
from markphotomediaapprovalstatuslib.public_portfolio.matching import match_record_to_public_assets
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset
from markphotomediaapprovalstatuslib.public_portfolio.banks import BANK_ADAPTERS
from markphotomediaapprovalstatuslib.status_handler import filter_records_by_bank_status
from save_bank_session import BLOCKED_BANKS, run_session_saver
from shared.file_operations import save_csv_with_backup


def _fetch_html(context, url: str, wait_ms: int = 10000, timeout_ms: int = 120000) -> str:
    """Fetch rendered page HTML using Playwright.

    :param context: Playwright browser context.
    :param url: URL to fetch.
    :param wait_ms: Milliseconds to wait after page load for JS rendering.
    :param timeout_ms: Page load timeout in milliseconds.
    :return: Rendered HTML content.
    """
    page = context.new_page()
    try:
        page.set_default_timeout(timeout_ms)
        page.goto(url, wait_until="load", timeout=timeout_ms)
        page.wait_for_timeout(wait_ms)
        return page.content()
    except Exception as exc:
        logging.warning("Failed to fetch %s: %s", url, exc)
        return ""
    finally:
        page.close()


def _fetch_html_with_scroll(
    context,
    url: str,
    max_scrolls: int = 30,
    scroll_wait_ms: int = 5000,
    initial_wait_ms: int = 10000,
    timeout_ms: int = 120000,
) -> str:
    """Fetch page HTML with infinite scroll to load all content.

    :param context: Playwright browser context.
    :param url: URL to fetch.
    :param max_scrolls: Maximum number of scroll attempts.
    :param scroll_wait_ms: Milliseconds to wait after each scroll.
    :param initial_wait_ms: Milliseconds to wait after initial page load.
    :param timeout_ms: Page load timeout in milliseconds.
    :return: Rendered HTML content with all loaded items.
    """
    page = context.new_page()
    try:
        page.set_default_timeout(timeout_ms)
        page.goto(url, wait_until="load", timeout=timeout_ms)
        page.wait_for_timeout(initial_wait_ms)

        prev_height = 0
        for _ in range(max_scrolls):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(scroll_wait_ms)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == prev_height:
                break
            prev_height = new_height

        return page.content()
    except Exception as exc:
        logging.warning("Failed to fetch with scroll %s: %s", url, exc)
        return ""
    finally:
        page.close()


def _find_next_page(html: str) -> Optional[str]:
    match = re.search(r"<link[^>]+rel=[\"']next[\"'][^>]+href=[\"']([^\"']+)[\"']", html, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"<a[^>]+rel=[\"']next[\"'][^>]+href=[\"']([^\"']+)[\"']", html, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _contributor_from_url(portfolio_url: str) -> str:
    """Derive a contributor identifier from the portfolio URL.

    :param portfolio_url: Portfolio page URL.
    :return: Contributor identifier string.
    """
    from urllib.parse import urlparse

    path = urlparse(portfolio_url).path.rstrip("/")
    last_segment = path.split("/")[-1] if "/" in path else path
    last_segment = re.sub(r"[_-]info$", "", last_segment)
    last_segment = re.sub(r"^profile[_-]?", "", last_segment)
    last_segment = re.sub(r"^portfolio[_-]?", "", last_segment)
    return last_segment or "owner"


def _crawl_portfolio(adapter, context, portfolio_url: str, contributor_id: str) -> Tuple[List[PublicAsset], bool]:
    """Crawl portfolio with infinite scroll to load all content.

    Uses scrolling to trigger lazy-loading of additional photos.
    Does NOT visit individual detail pages (they are often blocked by anti-bot).

    :param adapter: Bank adapter instance.
    :param context: Playwright browser context.
    :param portfolio_url: Portfolio page URL.
    :param contributor_id: Known contributor identifier.
    :return: Tuple of (assets, blocked_by_anti_bot).
    """
    logging.info("%s portfolio crawl with scroll: %s", adapter.bank, portfolio_url)
    html = _fetch_html_with_scroll(
        context,
        portfolio_url,
        max_scrolls=30,
        scroll_wait_ms=5000,
        initial_wait_ms=10000,
        timeout_ms=120000,
    )
    if len(html) < 5000:
        logging.warning("%s: portfolio page blocked by anti-bot (%d bytes)", adapter.bank, len(html))
        return [], True
    assets = adapter.extract_assets_from_portfolio(html, contributor_id)
    logging.info("%s: extracted %d assets after scrolling", adapter.bank, len(assets))
    return assets, False


def _crawl_bank_portfolio(
    adapter_cls,
    bank: str,
    headless: bool,
    portfolio_url: str,
    contributor_id: str,
) -> Tuple[List[PublicAsset], bool]:
    """Open a short-lived browser context, crawl one bank portfolio, and close it."""
    with browser_context(headless=headless, bank=bank) as context:
        adapter = adapter_cls(context)
        return _crawl_portfolio(adapter, context, portfolio_url, contributor_id)


def process_public_portfolio_approval(
    all_data: List[dict],
    filtered_data: List[dict],
    csv_path: str,
    config_path: Optional[str] = None,
    headless: bool = True,
    discover_only: bool = False,
) -> bool:
    """Process public portfolio approval detection for all supported banks.

    Creates separate browser contexts per bank to support bank-specific cookies.
    """
    config_path = config_path or DEFAULT_PUBLIC_PORTFOLIO_CONFIG
    config = load_config(config_path)
    config.setdefault("banks", {})
    changes_made = False
    summary = {
        "banks_scanned": 0,
        "approved_matches": 0,
        "ambiguous": 0,
        "blocked": 0,
    }

    for bank, adapter_cls in BANK_ADAPTERS.items():
        adapter = adapter_cls(None)
        if not adapter.is_supported():
            logging.info("%s: public portfolio mode not supported, skipping", bank)
            continue

        bank_records = filter_records_by_bank_status(filtered_data, bank, STATUS_CHECKED)
        if not bank_records:
            logging.debug("%s: no records with checked status, skipping", bank)
            continue

        bank_config = config["banks"].get(bank, {})
        portfolio_url = bank_config.get("portfolio_url") or DEFAULT_PORTFOLIO_URLS.get(bank)

        if not portfolio_url:
            logging.warning("%s: no portfolio URL configured, skipping.", bank)
            continue

        summary["banks_scanned"] += 1
        bank_changes = False

        contributor_id = bank_config.get("contributor_id") or _contributor_from_url(portfolio_url)
        assets, blocked = _crawl_bank_portfolio(
            adapter_cls,
            bank,
            headless,
            portfolio_url,
            contributor_id,
        )

        if blocked and bank in BLOCKED_BANKS:
            logging.info(
                "%s: triggering interactive session refresh to solve CAPTCHA and save cookies.",
                bank,
            )
            if run_session_saver(bank):
                assets, blocked = _crawl_bank_portfolio(
                    adapter_cls,
                    bank,
                    headless,
                    portfolio_url,
                    contributor_id,
                )
            else:
                logging.warning("%s: session refresh failed or was cancelled.", bank)

        if not assets:
            logging.warning(
                "%s: no assets found (blocked or empty). Run 'python save_bank_session.py --bank %s' to save cookies.",
                bank,
                bank,
            )
            summary["blocked"] += 1
            continue

        logging.info("%s: %d total assets from portfolio", bank, len(assets))

        if discover_only:
            continue

        for record in bank_records:
            title = record.get("Název", "")
            description = record.get("Popis", "")
            match = match_record_to_public_assets(bank, contributor_id, title, description, assets)

            if match.approved:
                status_column = f"{bank} {STATUS_COLUMN_KEYWORD}"
                if status_column in record and record[status_column] != STATUS_APPROVED:
                    record[status_column] = STATUS_APPROVED
                    changes_made = True
                    bank_changes = True
                    summary["approved_matches"] += 1
            elif match.matched_by == "AMBIGUOUS":
                summary["ambiguous"] += 1

        if bank_changes:
            save_csv_with_backup(all_data, csv_path)

    logging.info(
        "Public portfolio summary: banks=%s approved=%s ambiguous=%s blocked=%s",
        summary["banks_scanned"],
        summary["approved_matches"],
        summary["ambiguous"],
        summary["blocked"],
    )
    return changes_made
