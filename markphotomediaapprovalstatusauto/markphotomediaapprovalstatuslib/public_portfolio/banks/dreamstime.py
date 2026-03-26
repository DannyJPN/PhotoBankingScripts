"""Dreamstime public portfolio adapter."""

from __future__ import annotations

import re
from html import unescape
from typing import List

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset


class DreamstimeAdapter(BaseBankAdapter):
    bank = "Dreamstime"
    search_url_template = "https://www.dreamstime.com/search.php?srh_field={query}"
    item_url_regex = r'https?://(?:www\.)?dreamstime\.com/[^"\'\s>]*-image\d+'

    def extract_assets_from_portfolio(self, html: str, contributor_id: str) -> List[PublicAsset]:
        """Extract Dreamstime assets from portfolio or search-result pages.

        Dreamstime uses ``<a class="item__url ...">`` anchors with an inner
        ``<img>`` whose ``alt`` attribute carries the full title.  The ``aria-label``
        on the anchor is present but may be truncated, so the ``img alt`` is
        preferred.

        Falls back to the base-class ``_extract_title_near_link`` strategy when
        neither source yields a usable title.
        """
        assets: List[PublicAsset] = []
        seen: set = set()
        url_re = re.compile(self.item_url_regex, re.IGNORECASE)

        for url_match in url_re.finditer(html):
            url = url_match.group(0)
            if url in seen:
                continue

            pos = url_match.start()
            tag_open_start = html.rfind("<a", 0, pos)
            if tag_open_start == -1:
                continue
            tag_open_end = html.find(">", pos)
            if tag_open_end == -1:
                continue

            opening_tag = html[tag_open_start : tag_open_end + 1]
            close_pos = html.find("</a>", tag_open_end + 1)
            inner = html[tag_open_end + 1 : close_pos] if close_pos != -1 else ""

            alt_m = re.search(r'alt="([^"]{5,})"', inner, re.IGNORECASE)
            if alt_m:
                title = unescape(alt_m.group(1))
            else:
                aria_m = re.search(r'aria-label="([^"]+)"', opening_tag, re.IGNORECASE)
                title = unescape(aria_m.group(1)) if aria_m else ""

            if not title:
                title = self._extract_title_near_link(html, url)

            title = self._clean_title(title)
            if len(title) < 5:
                continue

            seen.add(url)
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
