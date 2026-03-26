"""Pixta discovery adapter.

Strategy: Playwright image-search UI.
"""

import logging
from typing import List

from markphotomediaapprovalstatuslib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatuslib.models import Candidate, PhotoRecord


class PixtaAdapter(BankDiscoveryAdapter):
    """Discover Pixta candidates via Playwright image-search UI."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "Pixta"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on Pixta for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement Playwright image-search UI
        logging.debug("PixtaAdapter.discover: not yet implemented for %s", record.file)
        return []
