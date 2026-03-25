"""Shutterstock public portfolio adapter."""

from __future__ import annotations

import re
from html import unescape
from typing import List
from urllib.parse import urljoin

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset


class ShutterstockAdapter(BaseBankAdapter):
    bank = "ShutterStock"
    search_url_template = "https://www.shutterstock.com/search/{query}"
    item_url_regex = r'(?:https?://(?:www\.)?shutterstock\.com)?/(?:[a-z]{2}/)?image-(?:photo|illustration|vector)/[^"\'\s>]+-\d+'

    def extract_item_links(self, html: str) -> List[str]:
        """Extract portfolio detail links, converting relative hrefs to absolute URLs."""
        links = re.findall(self.item_url_regex, html, flags=re.IGNORECASE)
        deduped: List[str] = []
        seen = set()
        for link in links:
            if not link.startswith("http"):
                link = urljoin("https://www.shutterstock.com", link)
            if link.endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            if link not in seen:
                deduped.append(link)
                seen.add(link)
        return deduped

    def extract_assets_from_portfolio(self, html: str, contributor_id: str) -> List[PublicAsset]:
        """Extract Shutterstock assets from clickable portfolio anchors.

        Tries three title sources in order:
        1. ``aria-label`` attribute on the opening ``<a>`` tag.
        2. ``alt`` attribute on an ``<img>`` inside the anchor.
        3. Visible text content inside the anchor after stripping tags.
        """
        assets: List[PublicAsset] = []
        seen = set()
        href_re = re.compile(
            r'href="(?P<href>(?:https?://(?:www\.)?shutterstock\.com)?/(?:[a-z]{2}/)?image-(?:photo|illustration|vector)/[^"\']+-\d+)"',
            re.IGNORECASE,
        )
        for href_match in href_re.finditer(html):
            url = href_match.group("href")
            if not url.startswith("http"):
                url = urljoin("https://www.shutterstock.com", url)
            if url in seen:
                continue

            pos = href_match.start()
            tag_open_start = html.rfind("<a", 0, pos)
            if tag_open_start == -1:
                continue
            tag_open_end = html.find(">", pos)
            if tag_open_end == -1:
                continue

            opening_tag = html[tag_open_start : tag_open_end + 1]
            aria_m = re.search(r'aria-label="([^"]+)"', opening_tag, re.IGNORECASE)
            title = aria_m.group(1) if aria_m else ""

            if not title:
                close_pos = html.find("</a>", tag_open_end + 1)
                inner = html[tag_open_end + 1 : close_pos] if close_pos != -1 else ""
                alt_m = re.search(r'alt="([^"]{5,})"', inner, re.IGNORECASE)
                if alt_m:
                    title = alt_m.group(1)
                else:
                    inner_text = re.sub(r"<[^>]+>", " ", inner)
                    title = unescape(re.sub(r"\s+", " ", inner_text)).strip()

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
            seen.add(url)
            self._log_discovered_asset(asset)
        return assets
