"""Getty Images discovery adapter.

Strategy: Playwright, enhanced_search=false.
"""

import logging
from typing import List

from markphotomediaapprovalstatusautolib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatusautolib.models import Candidate, PhotoRecord


class GettyImagesAdapter(BankDiscoveryAdapter):
    """Discover GettyImages candidates via Playwright."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "GettyImages"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on GettyImages for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement Playwright, enhanced_search=false
        logging.debug("GettyImagesAdapter.discover: not yet implemented for %s", record.file)
        return []
