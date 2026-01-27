"""Alamy public portfolio adapter."""

from __future__ import annotations

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter


class AlamyAdapter(BaseBankAdapter):
    bank = "Alamy"
    search_url_template = "https://www.alamy.com/stock-photo/{query}.html"
    item_url_regex = r'https?://(?:www\.)?alamy\.com/(?:stock-photo-|image-details/)[^"\'\s>]+\.html'
