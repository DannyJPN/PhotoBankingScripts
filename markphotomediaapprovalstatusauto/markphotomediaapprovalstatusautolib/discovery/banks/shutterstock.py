"""Shutterstock discovery adapter.

Strategy: portfolio page scraping (/g/USERNAME) + 260nw CDN thumbnail for pHash.
Free-tier API covers only a subset of the catalog and is NOT sufficient.
"""

import logging
from typing import List

from markphotomediaapprovalstatusautolib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatusautolib.models import Candidate, PhotoRecord


class ShutterStockAdapter(BankDiscoveryAdapter):
    """Discover ShutterStock candidates via public portfolio pages."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "ShutterStock"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on ShutterStock for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement portfolio scrape + 260nw CDN thumbnail extraction
        logging.debug("ShutterStockAdapter.discover: not yet implemented for %s", record.file)
        return []
