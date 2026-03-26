"""Registry mapping canonical bank names to their discovery adapter classes."""

import logging
from typing import Dict, List, Optional, Type

from markphotomediaapprovalstatusautolib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.adobestock import AdobeStockAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.alamy import AlamyAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.bigstockphoto import BigStockPhotoAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.canstockphoto import CanStockPhotoAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.depositphotos import DepositPhotosAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.dreamstime import DreamstimeAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.envato import EnvatoAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.freepik import FreepikAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.gettyimages import GettyImagesAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.mostphotos import MostPhotosAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.pixta import PixtaAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.pond5 import Pond5Adapter
from markphotomediaapprovalstatusautolib.discovery.banks.px500 import Px500Adapter
from markphotomediaapprovalstatusautolib.discovery.banks.rf123 import RF123Adapter
from markphotomediaapprovalstatusautolib.discovery.banks.shutterstock import ShutterStockAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.storyblocks import StoryBlocksAdapter
from markphotomediaapprovalstatusautolib.discovery.banks.vecteezy import VecteezyAdapter

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