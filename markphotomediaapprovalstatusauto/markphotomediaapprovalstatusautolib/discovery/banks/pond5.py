"""Pond5 discovery adapter.

Strategy: CDN HEAD check ec.pond5.com/s3/{padded_id}_iconm.jpeg.
"""

import logging
from typing import List

from markphotomediaapprovalstatusautolib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatusautolib.models import Candidate, PhotoRecord


class Pond5Adapter(BankDiscoveryAdapter):
    """Discover Pond5 candidates via CDN HEAD check."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "Pond5"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on Pond5 for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement CDN HEAD check ec.pond5.com/s3/{padded_id}_iconm.jpeg
        logging.debug("Pond5Adapter.discover: not yet implemented for %s", record.file)
        return []
