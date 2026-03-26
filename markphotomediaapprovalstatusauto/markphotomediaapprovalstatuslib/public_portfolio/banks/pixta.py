"""Pixta public portfolio adapter (not yet supported)."""

from __future__ import annotations

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import UnsupportedBankAdapter


class PixtaAdapter(UnsupportedBankAdapter):
    bank = "Pixta"
