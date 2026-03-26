"""Registry mapping canonical bank names to their discovery adapter classes."""

import logging
from typing import Dict, List, Optional, Type

from markphotomediaapprovalstatuslib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatuslib.discovery.banks.adobestock import AdobeStockAdapter
from markphotomediaapprovalstatuslib.discovery.banks.alamy import AlamyAdapter
from markphotomediaapprovalstatuslib.discovery.banks.bigstockphoto import BigStockPhotoAdapter
from markphotomediaapprovalstatuslib.discovery.banks.canstockphoto import CanStockPhotoAdapter
from markphotomediaapprovalstatuslib.discovery.banks.depositphotos import DepositPhotosAdapter
from markphotomediaapprovalstatuslib.discovery.banks.dreamstime import DreamstimeAdapter
from markphotomediaapprovalstatuslib.discovery.banks.envato import EnvatoAdapter
from markphotomediaapprovalstatuslib.discovery.banks.freepik import FreepikAdapter
from markphotomediaapprovalstatuslib.discovery.banks.gettyimages import GettyImagesAdapter
from markphotomediaapprovalstatuslib.discovery.banks.mostphotos import MostPhotosAdapter
from markphotomediaapprovalstatuslib.discovery.banks.pixta import PixtaAdapter
from markphotomediaapprovalstatuslib.discovery.banks.pond5 import Pond5Adapter
from markphotomediaapprovalstatuslib.discovery.banks.px500 import Px500Adapter
from markphotomediaapprovalstatuslib.discovery.banks.rf123 import RF123Adapter
from markphotomediaapprovalstatuslib.discovery.banks.shutterstock import ShutterStockAdapter
from markphotomediaapprovalstatuslib.discovery.banks.storyblocks import StoryBlocksAdapter
from markphotomediaapprovalstatuslib.discovery.banks.vecteezy import VecteezyAdapter

_REGISTRY: Dict[str, Type[BankDiscoveryAdapter]] = {
    "ShutterStock": ShutterStockAdapter,
    "AdobeStock": AdobeStockAdapter,
    "GettyImages": GettyImagesAdapter,
    "DepositPhotos": DepositPhotosAdapter,
    "Pond5": Pond5Adapter,
    "Dreamstime": DreamstimeAdapter,
    "123RF": RF123Adapter,
    "Freepik": FreepikAdapter,
    "Alamy": AlamyAdapter,
    "Vecteezy": VecteezyAdapter,
    "BigStockPhoto": BigStockPhotoAdapter,
    "StoryBlocks": StoryBlocksAdapter,
    "Envato": EnvatoAdapter,
    "Pixta": PixtaAdapter,
    "MostPhotos": MostPhotosAdapter,
    "500px": Px500Adapter,
    "CanStockPhoto": CanStockPhotoAdapter,
}


def get_adapter(bank_name: str) -> Optional[BankDiscoveryAdapter]:
    """Return an instantiated adapter for *bank_name*, or None if unknown.

    :param bank_name: Canonical bank name matching the CSV column prefix.
    :return: Instantiated BankDiscoveryAdapter, or None.
    """
    cls = _REGISTRY.get(bank_name)
    if cls is None:
        logging.warning("No discovery adapter registered for bank: %s", bank_name)
        return None
    return cls()


def available_banks() -> List[str]:
    """Return the sorted list of all registered bank names.

    :return: Sorted list of canonical bank name strings.
    """
    return sorted(_REGISTRY.keys())