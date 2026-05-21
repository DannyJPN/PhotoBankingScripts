"""Dreamstime discovery adapter.

Strategy: Playwright with session cookies for authenticated access.
"""

import logging
from typing import List

from markphotomediaapprovalstatusautolib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatusautolib.models import Candidate, PhotoRecord


class DreamstimeAdapter(BankDiscoveryAdapter):
    """Discover Dreamstime candidates via Playwright with session cookies."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "Dreamstime"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on Dreamstime for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement Playwright with session cookies
        logging.debug("DreamstimeAdapter.discover: not yet implemented for %s", record.file)
        return []
