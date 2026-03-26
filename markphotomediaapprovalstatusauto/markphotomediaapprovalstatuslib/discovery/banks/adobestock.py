"""Adobe Stock discovery adapter.

Strategy: API (httpx) or Playwright fallback, ftcdn.net thumbnails for pHash.
"""

import logging
from typing import List

from markphotomediaapprovalstatuslib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatuslib.models import Candidate, PhotoRecord


class AdobeStockAdapter(BankDiscoveryAdapter):
    """Discover AdobeStock candidates via API or Playwright fallback."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "AdobeStock"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on AdobeStock for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement API (httpx) or Playwright fallback, ftcdn.net thumbnails
        logging.debug("AdobeStockAdapter.discover: not yet implemented for %s", record.file)
        return []
