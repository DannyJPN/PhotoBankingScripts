#!/usr/bin/env python3
"""Save browser session cookies after manual CAPTCHA solving.

This script opens a browser to protected photobank pages.
The user manually solves any CAPTCHA challenges.
Once the page loads successfully, cookies are saved for later use.

Usage:
    python save_bank_session.py [--bank BANK]

Banks: ShutterStock, Pond5, BigStockPhoto, Dreamstime
"""

import argparse
import logging
import time
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

from markphotomediaapprovalstatuslib.constants import DEFAULT_LOG_DIR
from markphotomediaapprovalstatuslib.public_portfolio.config_store import load_effective_config
from markphotomediaapprovalstatuslib.public_portfolio.constants import DEFAULT_PUBLIC_PORTFOLIO_CONFIG
from shared.file_operations import ensure_directory, load_json_file, save_json_file
from shared.logging_config import setup_logging
from shared.utils import get_log_filename

logger = logging.getLogger(__name__)

BLOCKED_BANKS = ["ShutterStock", "Pond5", "BigStockPhoto", "Dreamstime"]
COOKIES_DIR = Path(__file__).parent / "cookies"


def _ensure_logging() -> None:
    """Initialize shared logging when running this helper standalone."""
    if logging.getLogger().handlers:
        return
    ensure_directory(DEFAULT_LOG_DIR)
    setup_logging(debug=False, log_file=get_log_filename(DEFAULT_LOG_DIR))


def _get_portfolio_url(bank: str, config_path: str = DEFAULT_PUBLIC_PORTFOLIO_CONFIG) -> Optional[str]:
    """Load the configured portfolio URL for a bank."""
    config = load_effective_config(config_path)
    return config.get("banks", {}).get(bank, {}).get("portfolio_url")


def _expected_title_fragment(portfolio_url: str) -> str:
    """Derive a stable title fragment from the configured portfolio URL."""
    path = urlparse(portfolio_url).path.rstrip("/").lower()
    if not path:
        return ""
    last_segment = path.split("/")[-1]
    last_segment = last_segment.replace("+", " ").replace("-", " ").replace("_", " ")
    last_segment = last_segment.replace("profile", "").replace("portfolio", "").replace("info", "")
    return " ".join(last_segment.split()).strip()


def get_cookies_path(bank: str) -> Path:
    """Get path to cookies file for a bank."""
    ensure_directory(COOKIES_DIR)
    return COOKIES_DIR / f"{bank.lower()}_cookies.json"


def save_cookies(bank: str, cookies: list) -> None:
    """Save cookies to file."""
    path = get_cookies_path(bank)
    save_json_file(str(path), cookies, indent=2, ensure_ascii=True)
    logger.info("Cookies saved to: %s", path)


def load_cookies(bank: str) -> Optional[list]:
    """Load cookies from file if exists."""
    path = get_cookies_path(bank)
    if not path.exists():
        return None
    return load_json_file(str(path))


def check_page_loaded(page, bank: str, portfolio_url: str) -> bool:
    """Check if the real page has loaded (not CAPTCHA/block page)."""
    try:
        body_len = page.evaluate("() => document.body.innerHTML.length")
        title = page.evaluate("() => document.title")
        expected_fragment = _expected_title_fragment(portfolio_url)

        if body_len > 50000:
            if expected_fragment and expected_fragment in title.lower():
                return True
            if bank == "BigStockPhoto" and body_len > 100000:
                return True
            if not expected_fragment and body_len > 100000:
                return True
        return False
    except Exception:
        return False


def run_session_saver(bank: str, timeout_sec: int = 300) -> bool:
    """Open browser and wait for user to solve CAPTCHA."""
    _ensure_logging()
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        logger.error("Playwright is required to save bank session cookies: %s", exc)
        return False

    url = _get_portfolio_url(bank)
    if not url:
        logger.error("No portfolio URL configured for %s", bank)
        return False

    logger.info("=" * 60)
    logger.info("SAVING SESSION FOR: %s", bank)
    logger.info("=" * 60)
    logger.info("")
    logger.info("1. Browser will open to: %s", url)
    logger.info("2. If you see a CAPTCHA, SOLVE IT MANUALLY")
    logger.info("3. Once the portfolio page loads, cookies will be saved")
    logger.info("4. Timeout: %d seconds", timeout_sec)
    logger.info("")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="cs-CZ",
        )
        page = context.new_page()

        logger.info("Opening page...")
        page.goto(url, wait_until="load", timeout=60000)

        start = time.time()
        while time.time() - start < timeout_sec:
            if check_page_loaded(page, bank, url):
                logger.info("")
                logger.info("SUCCESS! Page loaded correctly.")

                # Save cookies
                cookies = context.cookies()
                save_cookies(bank, cookies)
                logger.info("Saved %d cookies", len(cookies))

                # Show some page info
                title = page.evaluate("() => document.title")
                logger.info("Page title: %s", title)

                browser.close()
                return True

            elapsed = int(time.time() - start)
            remaining = timeout_sec - elapsed
            print(f"\r  Waiting for page load... {remaining}s remaining    ", end="", flush=True)
            time.sleep(2)

        print()
        logger.warning("TIMEOUT - page did not load within %d seconds", timeout_sec)
        logger.info("The CAPTCHA may not have been solved.")
        browser.close()
        return False


def main():
    _ensure_logging()
    parser = argparse.ArgumentParser(description="Save browser session cookies for photobanks")
    parser.add_argument(
        "--bank",
        choices=BLOCKED_BANKS + ["all"],
        default="all",
        help="Bank to save session for (default: all)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds (default: 300)",
    )
    args = parser.parse_args()

    banks = BLOCKED_BANKS if args.bank == "all" else [args.bank]

    results = {}
    for bank in banks:
        success = run_session_saver(bank, args.timeout)
        results[bank] = "OK" if success else "FAILED"
        logger.info("")

    logger.info("=" * 60)
    logger.info("RESULTS:")
    for bank, status in results.items():
        logger.info("  %s: %s", bank, status)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
