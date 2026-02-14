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
import json
import logging
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright

from markphotomediaapprovalstatuslib.public_portfolio.constants import DEFAULT_PORTFOLIO_URLS
from shared.file_operations import ensure_directory

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

BLOCKED_BANKS = ["ShutterStock", "Pond5", "BigStockPhoto", "Dreamstime"]
COOKIES_DIR = Path(__file__).parent / "cookies"


def get_cookies_path(bank: str) -> Path:
    """Get path to cookies file for a bank."""
    ensure_directory(COOKIES_DIR)
    return COOKIES_DIR / f"{bank.lower()}_cookies.json"


def save_cookies(bank: str, cookies: list) -> None:
    """Save cookies to file."""
    path = get_cookies_path(bank)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)
    logger.info("Cookies saved to: %s", path)


def load_cookies(bank: str) -> Optional[list]:
    """Load cookies from file if exists."""
    path = get_cookies_path(bank)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_page_loaded(page, bank: str) -> bool:
    """Check if the real page has loaded (not CAPTCHA/block page)."""
    try:
        body_len = page.evaluate("() => document.body.innerHTML.length")
        title = page.evaluate("() => document.title")

        if body_len > 50000:
            if bank == "ShutterStock" and "Danny" in title:
                return True
            if bank == "Pond5" and "dannyjpn" in title.lower():
                return True
            if bank == "BigStockPhoto" and body_len > 100000:
                return True
            if bank == "Dreamstime" and "dannjp" in title.lower():
                return True
        return False
    except Exception:
        return False


def run_session_saver(bank: str, timeout_sec: int = 300) -> bool:
    """Open browser and wait for user to solve CAPTCHA."""
    url = DEFAULT_PORTFOLIO_URLS.get(bank)
    if not url:
        logger.error("Unknown bank or no portfolio URL: %s", bank)
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
            if check_page_loaded(page, bank):
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