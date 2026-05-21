"""500px discovery adapter.

Strategy: low-priority Playwright stub (API removed 2018).
"""

import logging
from typing import List

from markphotomediaapprovalstatusautolib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatusautolib.models import Candidate, PhotoRecord


class Px500Adapter(BankDiscoveryAdapter):
    """Discover 500px candidates via Playwright (low-priority stub)."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "500px"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on 500px for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: low-priority Playwright stub (API zrušeno 2018)
        logging.debug("Px500Adapter.discover: not yet implemented for %s", record.file)
        return []
