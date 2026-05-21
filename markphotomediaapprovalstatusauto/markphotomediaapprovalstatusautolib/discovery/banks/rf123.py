"""123RF discovery adapter.

Strategy: httpx API with free-tier contributor key.
"""

import logging
from typing import List

from markphotomediaapprovalstatusautolib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatusautolib.models import Candidate, PhotoRecord


class RF123Adapter(BankDiscoveryAdapter):
    """Discover 123RF candidates via httpx API."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "123RF"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on 123RF for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement httpx API (bezplatný klíč)
        logging.debug("RF123Adapter.discover: not yet implemented for %s", record.file)
        return []
