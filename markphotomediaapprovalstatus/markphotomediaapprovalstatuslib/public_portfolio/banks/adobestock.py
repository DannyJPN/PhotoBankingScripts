"""Adobe Stock public portfolio adapter."""

from __future__ import annotations

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter


class AdobeStockAdapter(BaseBankAdapter):
    bank = "AdobeStock"
    search_url_template = "https://stock.adobe.com/search?k={query}"
    item_url_regex = r'https?://stock\.adobe\.com/(?:[a-z]{2}/)?(?:images|stock-photo)/[^"\'\s>]+/\d+'
