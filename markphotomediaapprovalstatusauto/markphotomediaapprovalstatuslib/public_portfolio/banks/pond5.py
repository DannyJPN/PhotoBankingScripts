"""Pond5 public portfolio adapter."""

from __future__ import annotations

import re
from html import unescape
from typing import List

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset


class Pond5Adapter(BaseBankAdapter):
    bank = "Pond5"
    search_url_template = "https://www.pond5.com/search?kw={query}&media=photos"
    item_url_regex = r'https?://(?:www\.)?pond5\.com/stock-images/photos/item/\d+[^"\'\s>]*'

    def extract_assets_from_portfolio(self, html: str, contributor_id: str) -> List[PublicAsset]:
        """Extract Pond5 photo assets from search result anchors."""
        assets: List[PublicAsset] = []
        seen = set()
        anchor_pattern = re.compile(
            r'<a[^>]+class="[^"]*SearchResultDSM[^"]*"[^>]*>',
            re.IGNORECASE,
        )
        href_pattern = re.compile(
            r'href="(https?://(?:www\.)?pond5\.com/stock-images/photos/item/\d+[^"\']*)"',
            re.IGNORECASE,
        )
        title_pattern = re.compile(r'title="([^"]+)"', re.IGNORECASE)
        aria_pattern = re.compile(r'aria-label="([^"]+)"', re.IGNORECASE)

        for match in anchor_pattern.finditer(html):
            tag = match.group(0)
            href_match = href_pattern.search(tag)
            if not href_match:
                continue
            url = href_match.group(1)
            if url in seen:
                continue
            title_match = title_pattern.search(tag)
            aria_match = aria_pattern.search(tag)
            title = ""
            if title_match:
                title = title_match.group(1)
            elif aria_match:
                title = aria_match.group(1)
            title = unescape(re.sub(r"\s+", " ", title)).strip()
            title = re.sub(r"\s+\d+$", "", title)
            if len(title) < 5:
                continue
            asset = PublicAsset(
                bank=self.bank,
                url=url,
                contributor_id=contributor_id,
                title=title,
                description="",
            )
            assets.append(asset)
            seen.add(url)
            self._log_discovered_asset(asset)
        return assets
