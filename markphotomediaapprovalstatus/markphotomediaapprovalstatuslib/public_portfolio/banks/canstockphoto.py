"""CanStockPhoto adapter (service closed)."""

from __future__ import annotations

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import UnsupportedBankAdapter


class CanStockPhotoAdapter(UnsupportedBankAdapter):
    bank = "CanStockPhoto"
