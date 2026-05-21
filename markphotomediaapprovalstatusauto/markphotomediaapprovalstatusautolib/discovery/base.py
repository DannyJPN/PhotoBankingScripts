"""Abstract base class for bank discovery adapters."""

from abc import ABC, abstractmethod
from typing import List

from markphotomediaapprovalstatusautolib.models import Candidate, PhotoRecord


class BankDiscoveryAdapter(ABC):
    """Interface that every bank adapter must implement.

    Each adapter is responsible for discovering Candidate objects on a single
    photobank for a given PhotoRecord.  The adapter must NOT make any approval
    decisions — it only returns raw candidates with enough data (preview URL,
    contributor name, asset ID) for the verification layer to work with.
    """

    @property
    @abstractmethod
    def bank_name(self) -> str:
        """Return the canonical bank name matching the CSV column prefix."""
        ...

    @abstractmethod
    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Return a list of Candidates that may correspond to *record*.

        :param record: The PhotoRecord to search for on this bank.
        :param kwargs: Optional extra arguments (http_client, headless, etc.).
        :return: List of Candidates, empty when none are found.
        """
        ...
