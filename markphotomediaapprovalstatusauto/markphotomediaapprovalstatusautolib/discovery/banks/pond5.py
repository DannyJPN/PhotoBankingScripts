"""Pond5 discovery adapter.

Strategy: crawl contributor portfolio page once (Playwright), extract all asset IDs,
then construct deterministic CDN preview URLs for pHash verification.

CDN URL pattern: https://ec.pond5.com/s3/{asset_id:09d}_iconm.jpeg
Portfolio URL:   https://www.pond5.com/artist/{contributor_name}
"""

import logging
import re
from typing import List, Optional, Tuple

from markphotomediaapprovalstatusautolib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatusautolib.models import Candidate, PhotoRecord
from markphotomediaapprovalstatusautolib.transport.browser_client import browser_context

_CDN_BASE = "https://ec.pond5.com/s3"
_PORTFOLIO_BASE = "https://www.pond5.com/artist"

# Matches asset IDs in href="/stock-footage/123456/" or "/stock-images/123456/"
_ASSET_ID_RE = re.compile(r'/stock-(?:footage|images|music|sfx|3d-models)/(\d+)/')


def build_cdn_preview_url(asset_id: int) -> str:
    """Return the CDN preview URL for a Pond5 asset.

    :param asset_id: Integer Pond5 asset identifier.
    :return: Full HTTPS URL to the medium preview JPEG (no auth required).
    """
    return f"{_CDN_BASE}/{asset_id:09d}_iconm.jpeg"


def crawl_pond5_portfolio(
    contributor_name: str,
    headless: bool = True,
    max_scrolls: int = 200,
) -> List[Tuple[int, str]]:
    """Crawl the Pond5 contributor portfolio and return all (asset_id, cdn_url) pairs.

    Uses Playwright infinite-scroll pagination to handle DataDome protection and
    JS-rendered content.  Stops when the page height stops growing or all
    IDs have been collected.

    :param contributor_name: Pond5 contributor username (used in portfolio URL).
    :param headless: Run browser headless when True.
    :param max_scrolls: Safety limit on scroll iterations.
    :return: List of (asset_id, cdn_preview_url) tuples for every portfolio asset.
    """
    portfolio_url = f"{_PORTFOLIO_BASE}/{contributor_name}"
    logging.info("Crawling Pond5 portfolio: %s", portfolio_url)

    seen_ids: set = set()
    assets: List[Tuple[int, str]] = []

    with browser_context(headless=headless) as ctx:
        page = ctx.new_page()
        try:
            page.goto(portfolio_url, timeout=30000)
            page.wait_for_timeout(3000)

            for iteration in range(max_scrolls):
                html = page.content()
                found_new = False

                for match in _ASSET_ID_RE.finditer(html):
                    asset_id = int(match.group(1))
                    if asset_id not in seen_ids:
                        seen_ids.add(asset_id)
                        assets.append((asset_id, build_cdn_preview_url(asset_id)))
                        found_new = True

                prev_height: int = page.evaluate("document.body.scrollHeight")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)
                new_height: int = page.evaluate("document.body.scrollHeight")

                if new_height == prev_height and not found_new:
                    logging.debug("No new content after scroll %d, stopping", iteration)
                    break

        finally:
            page.close()

    logging.info("Pond5 portfolio crawl complete: %d assets found", len(assets))
    return assets


class Pond5Adapter(BankDiscoveryAdapter):
    """Discover Pond5 candidates via portfolio crawl + CDN preview URLs.

    Requires a pre-built portfolio index passed as ``portfolio_index`` kwarg.
    When no index is provided the adapter returns an empty list (pipeline skips
    this bank until the index is built by :func:`crawl_pond5_portfolio`).
    """

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "Pond5"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Return Candidate objects for all assets in the portfolio index.

        The caller supplies the portfolio index built by
        :func:`crawl_pond5_portfolio`.  The evidence layer selects the best
        match by pHash distance.

        :param record: PhotoRecord to search for (used only for logging).
        :param kwargs:
            - ``portfolio_index`` (List[Tuple[int, str]]): list of
              (asset_id, cdn_preview_url) from :func:`crawl_pond5_portfolio`.
            - ``contributor_name`` (str): contributor username for identity matching.
        :return: List of Candidates (one per portfolio asset), or empty list
            when no index is provided.
        """
        portfolio_index: Optional[List[Tuple[int, str]]] = kwargs.get("portfolio_index")
        contributor_name: str = kwargs.get("contributor_name", "")

        if not portfolio_index:
            logging.debug("Pond5Adapter.discover: no portfolio_index for %s", record.file)
            return []

        candidates: List[Candidate] = []
        for asset_id, cdn_url in portfolio_index:
            candidates.append(
                Candidate(
                    bank=self.bank_name,
                    url=f"https://www.pond5.com/stock-footage/{asset_id}/",
                    preview_url=cdn_url,
                    contributor_name=contributor_name,
                    asset_id=str(asset_id),
                )
            )
        return candidates