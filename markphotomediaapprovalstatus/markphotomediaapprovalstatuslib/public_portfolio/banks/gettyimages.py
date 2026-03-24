"""Getty Images (iStock) public portfolio adapter."""

from __future__ import annotations

import re
from typing import List

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset


class GettyImagesAdapter(BaseBankAdapter):
    bank = "GettyImages"
    search_url_template = "https://www.istockphoto.com/search/2/image?phrase={query}"
    item_url_regex = (
        r'https?://(?:www\.)?istockphoto\.com/(?:[a-z]{2}/)?'
        r'(?:fotografie|photo|illustration|vector|vektor|foto)/[^"\'\s>]+-gm\d+-\d+'
    )

    def extract_assets_from_portfolio(self, html: str, contributor_id: str) -> List[PublicAsset]:
        """Extract assets from iStock portfolio using alt text and photo URLs.

        iStock uses:
        - URLs like /en/photo/title-words-here-gm123456789-123456789
        - Alt text with full titles ending in "stock photo"
        """
        assets: List[PublicAsset] = []
        seen_ids: set = set()
        link_pattern = r'/(?:[a-z]{2}/)?photo/([a-z0-9-]+)-gm(\d+)-\d+'
        link_matches = re.findall(link_pattern, html, re.IGNORECASE)
        for title_slug, photo_id in link_matches:
            if photo_id in seen_ids:
                continue
            seen_ids.add(photo_id)
            title = title_slug.replace("-", " ").strip()
            if len(title) < 5:
                continue
            url = f"https://www.istockphoto.com/en/photo/{title_slug}-gm{photo_id}"
            asset = PublicAsset(
                bank=self.bank,
                url=url,
                contributor_id=contributor_id,
                title=self._clean_title(title.capitalize()),
                description="",
            )
            assets.append(asset)
            self._log_discovered_asset(asset)
        return assets
