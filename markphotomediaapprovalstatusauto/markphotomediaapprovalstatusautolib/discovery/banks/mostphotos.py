"""MostPhotos discovery adapter.

Strategy: Playwright item pages.
"""

import logging
from typing import List

from markphotomediaapprovalstatusautolib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatusautolib.models import Candidate, PhotoRecord


class MostPhotosAdapter(BankDiscoveryAdapter):
    """Discover MostPhotos candidates via Playwright item pages."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "MostPhotos"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on MostPhotos for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement Playwright item pages
        logging.debug("MostPhotosAdapter.discover: not yet implemented for %s", record.file)
        return []
