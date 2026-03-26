"""Alamy discovery adapter.

Strategy: Playwright (portfolio feature removed 02/2025).
"""

import logging
from typing import List

from markphotomediaapprovalstatuslib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatuslib.models import Candidate, PhotoRecord


class AlamyAdapter(BankDiscoveryAdapter):
    """Discover Alamy candidates via Playwright."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "Alamy"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on Alamy for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement Playwright (portfolio zrušeno 02/2025)
        logging.debug("AlamyAdapter.discover: not yet implemented for %s", record.file)
        return []
