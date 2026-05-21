"""Vecteezy discovery adapter.

Strategy: httpx API or low-priority Playwright fallback.
"""

import logging
from typing import List

from markphotomediaapprovalstatusautolib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatusautolib.models import Candidate, PhotoRecord


class VecteezyAdapter(BankDiscoveryAdapter):
    """Discover Vecteezy candidates via httpx API or Playwright fallback."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "Vecteezy"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on Vecteezy for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement httpx API or low-priority fallback
        logging.debug("VecteezyAdapter.discover: not yet implemented for %s", record.file)
        return []
