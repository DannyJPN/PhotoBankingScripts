"""Adobe Stock public portfolio adapter."""

from __future__ import annotations

import re
from typing import List

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset


class AdobeStockAdapter(BaseBankAdapter):
    bank = "AdobeStock"
    search_url_template = "https://stock.adobe.com/search?k={query}"
    item_url_regex = r'https?://stock\.adobe\.com/(?:[a-z]{2}/)?(?:images|stock-photo)/[^"\'\s>]+/\d+'

    def extract_assets_from_portfolio(self, html: str, contributor_id: str) -> List[PublicAsset]:
        """Extract Adobe Stock assets using the title slug embedded in the image URL.

        Adobe Stock image URLs follow the pattern:
        ``https://stock.adobe.com/images/title-words-here/12345678``
        The slug before the numeric ID is used as the title source.

        Falls back to ``alt`` text or ``aria-label`` near the link when the
        slug alone is too short.
        """
        assets: List[PublicAsset] = []
        seen_ids: set = set()
        url_re = re.compile(self.item_url_regex, re.IGNORECASE)
        slug_re = re.compile(
            r'/(?:images|stock-photo)/([a-z0-9][a-z0-9-]*)/(\d+)',
            re.IGNORECASE,
        )

        for url_match in url_re.finditer(html):
            url = url_match.group(0)
            slug_m = slug_re.search(url)
            if not slug_m:
                continue
            photo_id = slug_m.group(2)
            if photo_id in seen_ids:
                continue
            seen_ids.add(photo_id)

            title_from_slug = slug_m.group(1).replace("-", " ").strip()
            title = title_from_slug.capitalize() if len(title_from_slug) >= 5 else ""

            if not title:
                title = self._extract_title_near_link(html, url)

            title = self._clean_title(title)
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
            self._log_discovered_asset(asset)

        return assets
