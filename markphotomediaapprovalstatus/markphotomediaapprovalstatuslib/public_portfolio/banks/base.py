"""Base adapter for public portfolio crawling."""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset
from markphotomediaapprovalstatuslib.public_portfolio.utils import (
    extract_from_json_ld,
    extract_meta_content,
    extract_title,
)


class BaseBankAdapter:
    bank = "Base"
    search_url_template: Optional[str] = None
    item_url_regex: Optional[str] = None
    contributor_regex: Optional[str] = None

    def __init__(self, browser_context):
        self.browser_context = browser_context

    def is_supported(self) -> bool:
        """Whether this bank supports public portfolio approval detection."""
        return True

    def build_search_url(self, query: str) -> Optional[str]:
        """Build search URL from query string."""
        if not self.search_url_template:
            return None
        return self.search_url_template.format(query=query)

    def extract_item_links(self, html: str) -> List[str]:
        """Extract item detail links from search results HTML."""
        if not self.item_url_regex:
            return []
        links = re.findall(self.item_url_regex, html, flags=re.IGNORECASE)
        deduped: List[str] = []
        seen = set()
        for link in links:
            if link not in seen:
                deduped.append(link)
                seen.add(link)
        return deduped

    def extract_assets_from_portfolio(self, html: str, contributor_id: str) -> List[PublicAsset]:
        """Extract assets directly from the portfolio page HTML without visiting detail pages.

        Uses alt text, aria-label, or other metadata available on the portfolio listing.
        Subclasses should override this for bank-specific extraction.

        :param html: Rendered HTML of the portfolio page.
        :param contributor_id: Known contributor identifier.
        :return: List of PublicAsset objects with available metadata.
        """
        assets: List[PublicAsset] = []
        links = self.extract_item_links(html)
        for url in links:
            title = self._extract_title_near_link(html, url)
            if title:
                asset = PublicAsset(
                    bank=self.bank,
                    url=url,
                    contributor_id=contributor_id,
                    title=title,
                    description="",
                )
                assets.append(asset)
                self._log_discovered_asset(asset)
        return assets

    def _log_discovered_asset(self, asset: PublicAsset) -> None:
        """Log a discovered portfolio asset for debug runs."""
        if asset.url:
            logging.debug("%s: discovered portfolio asset %s", self.bank, asset.url)
        else:
            logging.debug("%s: discovered portfolio asset without URL (title=%s)", self.bank, asset.title)

    def _extract_title_near_link(self, html: str, url: str) -> str:
        """Extract title from alt or aria-label near a link in the HTML.

        :param html: Full page HTML.
        :param url: The item URL to find context for.
        :return: Extracted title or empty string.
        """
        escaped_url = re.escape(url)
        pattern = rf'<a[^>]*href="{escaped_url}"[^>]*>(.*?)</a>'
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if match:
            inner = match.group(1)
            alt_match = re.search(r'alt="([^"]+)"', inner, re.IGNORECASE)
            if alt_match:
                return self._clean_title(alt_match.group(1))
        aria_pattern = rf'<a[^>]*href="{escaped_url}"[^>]*aria-label="([^"]+)"'
        aria_match = re.search(aria_pattern, html, re.IGNORECASE)
        if aria_match:
            return self._clean_title(aria_match.group(1))
        return ""

    def _clean_title(self, raw_title: str) -> str:
        """Remove common suffixes added by photobanks to alt text.

        :param raw_title: Raw title string from alt/aria-label.
        :return: Cleaned title.
        """
        suffixes = [
            " royalty free stock photos",
            " royalty free stock photo",
            " stock photography",
            " stock fotka",
            " stock photo, image",
            " stock photo",
            " stock image",
            " — stock photo, image",
        ]
        title = raw_title.strip()
        lower = title.lower()
        for suffix in suffixes:
            if lower.endswith(suffix):
                title = title[: len(title) - len(suffix)]
                break
        return title.strip()

    def extract_public_asset(self, url: str, html: str) -> Optional[PublicAsset]:
        """Extract asset metadata from a detail page.

        :param url: URL of the detail page.
        :param html: Rendered HTML of the detail page.
        :return: PublicAsset or None if extraction fails.
        """
        data = extract_from_json_ld(html)
        title = data.get("title") or extract_meta_content(html, "og:title") or extract_title(html) or ""
        description = data.get("description") or extract_meta_content(html, "og:description") or ""
        contributor = data.get("author")
        if not contributor and self.contributor_regex:
            match = re.search(self.contributor_regex, html, re.IGNORECASE)
            if match:
                contributor = match.group(1).strip()
        if not contributor:
            logging.debug("%s: contributor not found for %s", self.bank, url)
            return None
        return PublicAsset(
            bank=self.bank,
            url=url,
            contributor_id=contributor,
            title=title,
            description=description,
        )


class UnsupportedBankAdapter(BaseBankAdapter):
    """Base for banks without public portfolio support (new or deprecated)."""

    def is_supported(self) -> bool:
        """Not supported for public portfolio detection."""
        return False

