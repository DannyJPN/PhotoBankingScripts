"""Shutterstock public portfolio adapter."""

from __future__ import annotations

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter


class ShutterstockAdapter(BaseBankAdapter):
    bank = "ShutterStock"
    search_url_template = "https://www.shutterstock.com/search/{query}"
    item_url_regex = r'https?://(?:www\.)?shutterstock\.com/image-(?:photo|illustration|vector)/[^"\'\s>]+-\d+'
