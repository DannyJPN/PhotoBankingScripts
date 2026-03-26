"""Envato discovery adapter.

Strategy: Market API vs Elements web scraping.
"""

import logging
from typing import List

from markphotomediaapprovalstatuslib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatuslib.models import Candidate, PhotoRecord


class EnvatoAdapter(BankDiscoveryAdapter):
    """Discover Envato candidates via Market API or Elements web."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "Envato"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on Envato for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement Market API vs Elements web
        logging.debug("EnvatoAdapter.discover: not yet implemented for %s", record.file)
        return []
