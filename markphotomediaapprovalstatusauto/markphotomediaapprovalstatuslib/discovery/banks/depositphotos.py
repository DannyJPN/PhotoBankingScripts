"""DepositPhotos discovery adapter.

Strategy: __NEXT_DATA__ JSON parse + static CDN for thumbnails.
"""

import logging
from typing import List

from markphotomediaapprovalstatuslib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatuslib.models import Candidate, PhotoRecord


class DepositPhotosAdapter(BankDiscoveryAdapter):
    """Discover DepositPhotos candidates via __NEXT_DATA__ JSON parse."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "DepositPhotos"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on DepositPhotos for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement __NEXT_DATA__ JSON parse + static CDN
        logging.debug("DepositPhotosAdapter.discover: not yet implemented for %s", record.file)
        return []
