"""Bigstock public portfolio adapter (deprecated but still functional)."""

from __future__ import annotations

import re
from typing import List

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset


class BigStockPhotoAdapter(BaseBankAdapter):
    bank = "BigStockPhoto"
    search_url_template = "https://www.bigstockphoto.com/search/{query}/"
    item_url_regex = r'https?://(?:www\.)?bigstockphoto\.com/image-\d+/[^"\'\s>]+'

    def extract_assets_from_portfolio(self, html: str, contributor_id: str) -> List[PublicAsset]:
        """Extract assets from BigStockPhoto portfolio page.

        BigStock uses image URLs with pattern:
        /image-NNNNNN/title-words-here
        """
        assets: List[PublicAsset] = []
        seen_ids: set = set()
        pattern = r'/image-(\d+)/([a-z0-9-]+)'
        matches = re.findall(pattern, html, re.IGNORECASE)
        for photo_id, title_slug in matches:
            if photo_id in seen_ids:
                continue
            seen_ids.add(photo_id)
            title = title_slug.replace("-", " ").strip()
            if len(title) < 5:
                continue
            url = f"https://www.bigstockphoto.com/image-{photo_id}/{title_slug}"
            assets.append(PublicAsset(
                bank=self.bank,
                url=url,
                contributor_id=contributor_id,
                title=self._clean_title(title.capitalize()),
                description="",
            ))
        return assets