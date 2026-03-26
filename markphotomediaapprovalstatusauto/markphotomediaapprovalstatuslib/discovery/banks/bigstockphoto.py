"""BigStockPhoto discovery adapter.

Strategy: Playwright contributor search.
"""

import logging
from typing import List

from markphotomediaapprovalstatuslib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatuslib.models import Candidate, PhotoRecord


class BigStockPhotoAdapter(BankDiscoveryAdapter):
    """Discover BigStockPhoto candidates via Playwright contributor search."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "BigStockPhoto"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on BigStockPhoto for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement Playwright contributor search
        logging.debug("BigStockPhotoAdapter.discover: not yet implemented for %s", record.file)
        return []
