"""Playwright browser wrapper for public portfolio crawling."""

from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING, Iterator, List, Optional

from markphotomediaapprovalstatuslib.public_portfolio.constants import COOKIES_DIR
from shared.file_operations import load_json_file

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext


def load_cookies_for_bank(bank: str) -> Optional[List[dict]]:
    """Load saved cookies for a bank if available.

    :param bank: Bank name (e.g., "ShutterStock").
    :return: List of cookie dicts or None.
    """
    cookies_file = COOKIES_DIR / f"{bank.lower()}_cookies.json"
    if not cookies_file.exists():
        return None
    try:
        cookies = load_json_file(str(cookies_file))
        logging.debug("Loaded %d cookies for %s", len(cookies), bank)
        return cookies
    except Exception as exc:
        logging.warning("Failed to load cookies for %s: %s", bank, exc)
        return None


@contextlib.contextmanager
def browser_context(headless: bool = True, bank: Optional[str] = None) -> Iterator["BrowserContext"]:
    """Create a Playwright browser context for portfolio crawling.

    :param headless: Whether to run headless.
    :param bank: Optional bank name to load saved cookies for.
    :yield: Playwright BrowserContext.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("Playwright is required for public portfolio mode.") from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="cs-CZ",
        )
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        if bank:
            cookies = load_cookies_for_bank(bank)
            if cookies:
                try:
                    context.add_cookies(cookies)
                    logging.info("%s: loaded %d saved cookies", bank, len(cookies))
                except Exception as exc:
                    logging.warning("%s: failed to add cookies: %s", bank, exc)

        try:
            yield context
        finally:
            context.close()
            browser.close()
