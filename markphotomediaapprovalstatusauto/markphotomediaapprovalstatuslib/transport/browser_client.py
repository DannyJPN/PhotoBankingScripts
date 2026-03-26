"""Playwright browser transport layer."""

import logging
from contextlib import contextmanager
from typing import Generator, List, Optional

from playwright.sync_api import BrowserContext, sync_playwright


@contextmanager
def browser_context(
    headless: bool = True,
    session_cookies: Optional[List[dict]] = None,
) -> Generator[BrowserContext, None, None]:
    """Context manager providing a Playwright browser context.

    :param headless: Run browser in headless mode when True.
    :param session_cookies: Optional list of cookies to inject (for banks
        requiring authentication such as Dreamstime).
    :yields: A configured Playwright BrowserContext.
    """
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(locale="en-US")
        if session_cookies:
            context.add_cookies(session_cookies)
        try:
            yield context
        finally:
            context.close()
            browser.close()


def fetch_html(
    context: BrowserContext,
    url: str,
    wait_ms: int = 3000,
    timeout_ms: int = 30000,
) -> str:
    """Fetch fully rendered HTML for *url* using Playwright.

    :param context: Active Playwright BrowserContext.
    :param url: Target URL.
    :param wait_ms: Milliseconds to wait after page load for JS rendering.
    :param timeout_ms: Page navigation timeout in milliseconds.
    :return: Rendered HTML string.
    :raises playwright.sync_api.TimeoutError: If navigation exceeds timeout.
    """
    page = context.new_page()
    try:
        logging.debug("Fetching HTML via browser: %s", url)
        page.goto(url, timeout=timeout_ms)
        page.wait_for_timeout(wait_ms)
        return page.content()
    finally:
        page.close()
