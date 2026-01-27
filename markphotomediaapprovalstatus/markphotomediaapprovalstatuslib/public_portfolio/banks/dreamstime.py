"""Dreamstime public portfolio adapter."""

from __future__ import annotations

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter


class DreamstimeAdapter(BaseBankAdapter):
    bank = "Dreamstime"
    search_url_template = "https://www.dreamstime.com/search.php?srh_field={query}"
    item_url_regex = r'https?://(?:www\.)?dreamstime\.com/[^"\'\s>]*-image\d+'
