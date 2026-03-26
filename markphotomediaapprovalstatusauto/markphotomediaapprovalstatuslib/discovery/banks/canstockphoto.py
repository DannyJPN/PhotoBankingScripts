"""CanStockPhoto discovery adapter.

NOTE: Service closed permanently in October 2023. Always returns empty list.
"""

import logging
from typing import List

from markphotomediaapprovalstatuslib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatuslib.models import Candidate, PhotoRecord


class CanStockPhotoAdapter(BankDiscoveryAdapter):
    """CanStockPhoto adapter — service closed 10/2023, always returns empty list."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "CanStockPhoto"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Return empty list; CanStockPhoto service closed October 2023.

        :param record: PhotoRecord to search for.
        :return: Always an empty list.
        """
        logging.debug("CanStockPhotoAdapter.discover: service closed 10/2023, skipping %s", record.file)
        return []
