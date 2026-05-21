"""Save browser session cookies after manual CAPTCHA solving.

Opens a visible browser to the bank's portfolio URL.
The user manually solves any CAPTCHA challenge.
Once the page loads successfully, cookies are saved to cookies/{bank}.json
for use in subsequent automated runs.

Usage:
    python save_bank_session.py --bank Pond5
    python save_bank_session.py --bank Pond5 --timeout 600
"""

import argparse
import json
import logging
import os
import sys
import time

from playwright.sync_api import sync_playwright

from shared.file_operations import ensure_directory, load_json_file
from shared.logging_config import setup_logging
from shared.utils import get_log_filename

from markphotomediaapprovalstatusautolib.constants import DEFAULT_LOG_DIR

_PORTFOLIOS_JSON = os.path.join(os.path.dirname(__file__), "..", "markphotomediaapprovalstatus", "public_portfolios.json")
_COOKIES_DIR = os.path.join(os.path.dirname(__file__), "cookies")

BLOCKED_BANKS = ["ShutterStock", "Pond5", "Dreamstime"]


def save_session(bank: str, portfolio_url: str, timeout_seconds: int) -> bool:
    """Open a persistent Chromium profile for *bank*, wait for manual navigation, save cookies.

    Uses ``launch_persistent_context`` so Chromium retains real browser state
    (fingerprint, history, cookies) between runs — this bypasses DataDome fingerprint
    detection that blocks fresh Playwright contexts.

    The browser stays open until the portfolio page is confirmed loaded (HTML > 10 KB),
    or until *timeout_seconds* expires.

    :param bank: Canonical bank name.
    :param portfolio_url: Full portfolio URL to navigate to.
    :param timeout_seconds: Maximum seconds to wait for successful page load.
    :return: True if cookies were saved successfully, False otherwise.
    """
    cookies_path = os.path.join(_COOKIES_DIR, f"{bank}.json")
    profile_dir = os.path.join(_COOKIES_DIR, f"profile_{bank}")
    ensure_directory(_COOKIES_DIR)
    ensure_directory(profile_dir)

    logging.info("Opening persistent browser for %s: %s", bank, portfolio_url)
    logging.info("Browse normally — solve any CAPTCHA if shown. Script saves cookies once portfolio page loads.")
    logging.info("Profile stored at: %s", profile_dir)

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            locale="en-US",
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        page = context.new_page()

        try:
            page.goto(portfolio_url, timeout=30000)
        except Exception as exc:
            logging.warning("Initial navigation error (continuing): %s", exc)

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            time.sleep(3)
            try:
                html = page.content()
            except Exception:
                time.sleep(3)
                continue

            if len(html) > 10000:
                logging.info("Portfolio page loaded (len=%d). Saving cookies.", len(html))
                cookies = context.cookies()
                with open(cookies_path, "w", encoding="utf-8") as fh:
                    json.dump(cookies, fh, indent=2)
                logging.info("Cookies saved to: %s (%d cookies)", cookies_path, len(cookies))
                context.close()
                return True

            logging.debug("Waiting for page to load (len=%d)...", len(html))

        logging.error("Timeout after %ds. Portfolio page did not load — CAPTCHA not solved.", timeout_seconds)
        context.close()
        return False


def load_portfolio_url(bank: str) -> str:
    """Load the portfolio URL for *bank* from public_portfolios.json.

    :param bank: Canonical bank name.
    :return: Portfolio URL string.
    :raises SystemExit: If JSON file or bank entry is missing.
    """
    try:
        data = load_json_file(_PORTFOLIOS_JSON)
        url = data["banks"][bank]["portfolio_url"]
        return url
    except (FileNotFoundError, KeyError) as exc:
        logging.error("Cannot load portfolio URL for %s from %s: %s", bank, _PORTFOLIOS_JSON, exc)
        sys.exit(1)


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments.

    :return: Parsed namespace.
    """
    parser = argparse.ArgumentParser(description="Save browser session cookies for photobanks requiring CAPTCHA.")
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
        help="Seconds to wait for manual CAPTCHA solve (default: 300)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--log-dir", type=str, default=DEFAULT_LOG_DIR)
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_arguments()
    ensure_directory(args.log_dir)
    setup_logging(debug=args.debug, log_file=get_log_filename(args.log_dir))

    banks = BLOCKED_BANKS if args.bank == "all" else [args.bank]
    results = {}

    for bank in banks:
        url = load_portfolio_url(bank)
        success = save_session(bank, url, args.timeout)
        results[bank] = "OK" if success else "FAILED"

    logging.info("=" * 50)
    for bank, status in results.items():
        logging.info("  %s: %s", bank, status)
    logging.info("=" * 50)


if __name__ == "__main__":
    main()