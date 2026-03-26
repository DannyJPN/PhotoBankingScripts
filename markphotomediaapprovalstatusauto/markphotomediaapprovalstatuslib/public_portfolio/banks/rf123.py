"""123RF public portfolio adapter."""

from __future__ import annotations

import re
from typing import List
from urllib.parse import urljoin

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset


class RF123Adapter(BaseBankAdapter):
    bank = "123RF"
    search_url_template = "https://www.123rf.com/stock-photo/{query}.html"
    item_url_regex = r'(?:https?://(?:[a-z]{2}\.)?123rf\.com)?/(?:photo|vector|illustration)_\d+[^"\'\s>]*\.html'

    def extract_item_links(self, html: str) -> List[str]:
        """Extract item links, converting relative paths to absolute URLs."""
        if not self.item_url_regex:
            return []
        links = re.findall(self.item_url_regex, html, flags=re.IGNORECASE)
        base_url = "https://www.123rf.com"
        deduped: List[str] = []
        seen = set()
        for link in links:
            if not link.startswith("http"):
                link = urljoin(base_url, link)
            if link not in seen:
                deduped.append(link)
                seen.add(link)
        return deduped

    def extract_assets_from_portfolio(self, html: str, contributor_id: str) -> List[PublicAsset]:
        """Extract assets from 123RF portfolio using img title attributes.

        123RF uses <img title="Description text"> for photo descriptions.
        Photo URLs are like /photo_123456789_title-words-here.html
        """
        assets: List[PublicAsset] = []
        seen_ids: set = set()
        link_pattern = r'/photo_(\d+)_([a-z0-9-]+)\.html'
        link_matches = re.findall(link_pattern, html, re.IGNORECASE)
        for photo_id, title_slug in link_matches:
            if photo_id in seen_ids:
                continue
            seen_ids.add(photo_id)
            title_from_slug = title_slug.replace("-", " ").strip()
            if len(title_from_slug) < 5:
                continue
            url = f"https://www.123rf.com/photo_{photo_id}_{title_slug}.html"
            asset = PublicAsset(
                bank=self.bank,
                url=url,
                contributor_id=contributor_id,
                title=title_from_slug.capitalize(),
                description="",
            )
            assets.append(asset)
            self._log_discovered_asset(asset)
        return assets
