"""Freepik discovery adapter.

Strategy: httpx API via api.freepik.com.
"""

import logging
from typing import List

from markphotomediaapprovalstatuslib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatuslib.models import Candidate, PhotoRecord


class FreepikAdapter(BankDiscoveryAdapter):
    """Discover Freepik candidates via httpx API."""

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "Freepik"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Discover candidates on Freepik for *record*.

        :param record: PhotoRecord to search for.
        :return: List of Candidates found. Currently returns empty list (not yet implemented).
        """
        # TODO: implement httpx API api.freepik.com
        logging.debug("FreepikAdapter.discover: not yet implemented for %s", record.file)
        return []
