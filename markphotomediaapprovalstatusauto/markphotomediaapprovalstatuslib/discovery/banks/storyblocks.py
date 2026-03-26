"""StoryBlocks discovery adapter.

Strategy: httpx if API keys are available.
"""

import logging
from typing import List

from markphotomediaapprovalstatuslib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatuslib.models import Candidate, PhotoRecord


class StoryBlocksAdapter(BankDiscoveryAdapter):
    """Discover StoryBlocks candidates via httpx API."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "StoryBlocks"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on StoryBlocks for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement httpx pokud klíče dostupné
        logging.debug("StoryBlocksAdapter.discover: not yet implemented for %s", record.file)
        return []
