"""Pond5 public portfolio adapter."""

from __future__ import annotations

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter


class Pond5Adapter(BaseBankAdapter):
    bank = "Pond5"
    search_url_template = "https://www.pond5.com/search?kw={query}&media=photos"
    item_url_regex = r'https?://(?:www\.)?pond5\.com/(?:stock-photo|stock-footage|stock-video|stock-music)/item/\d+'
