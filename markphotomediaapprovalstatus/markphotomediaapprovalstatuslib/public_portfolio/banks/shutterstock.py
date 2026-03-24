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
        """Extract Shutterstock assets from clickable portfolio anchors."""
        assets: List[PublicAsset] = []
        seen = set()
        pattern = re.compile(
            r'<a[^>]+href="(?P<href>(?:https?://(?:www\.)?shutterstock\.com)?/(?:[a-z]{2}/)?image-(?:photo|illustration|vector)/[^"\']+-\d+)"'
            r'[^>]*(?:aria-label="(?P<aria>[^"]+)")?[^>]*>(?P<inner>.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(html):
            url = match.group("href")
            if not url.startswith("http"):
                url = urljoin("https://www.shutterstock.com", url)
            if url in seen:
                continue

            title = match.group("aria") or ""
            if not title:
                inner_text = re.sub(r"<[^>]+>", " ", match.group("inner"))
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
