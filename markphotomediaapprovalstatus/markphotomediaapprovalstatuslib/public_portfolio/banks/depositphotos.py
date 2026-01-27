"""Depositphotos public portfolio adapter."""

from __future__ import annotations

import re
from typing import List
from urllib.parse import urljoin

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset
from markphotomediaapprovalstatuslib.public_portfolio.matching import extract_xid


class DepositPhotosAdapter(BaseBankAdapter):
    bank = "DepositPhotos"
    search_url_template = "https://depositphotos.com/photos/{query}.html"
    item_url_regex = r'(?:https?://(?:www\.)?depositphotos\.com)?/(?:photo|vector)/[^"\'\s>]+-\d+\.html'

    def extract_item_links(self, html: str) -> List[str]:
        """Extract item links, converting relative paths to absolute URLs."""
        if not self.item_url_regex:
            return []
        links = re.findall(self.item_url_regex, html, flags=re.IGNORECASE)
        base_url = "https://depositphotos.com"
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
        """Extract assets from DepositPhotos portfolio using image URLs with embedded titles.

        DepositPhotos uses image URLs with pattern:
        depositphotos_NNNNNN-stock-photo-title-words-here.jpg
        """
        assets: List[PublicAsset] = []
        seen_ids: set = set()
        pattern = r'depositphotos_(\d+)-stock-(?:photo|illustration|vector)-([a-z0-9-]+)\.(?:jpg|png|webp)'
        matches = re.findall(pattern, html, re.IGNORECASE)
        for photo_id, title_slug in matches:
            if photo_id in seen_ids:
                continue
            seen_ids.add(photo_id)
            title = title_slug.replace("-", " ").strip().capitalize()
            if len(title) < 5:
                continue
            url = f"https://depositphotos.com/photo/{title_slug}-{photo_id}.html"
            assets.append(PublicAsset(
                bank=self.bank,
                url=url,
                contributor_id=contributor_id,
                title=title,
                description="",
                xid=extract_xid(title),
            ))
        return assets