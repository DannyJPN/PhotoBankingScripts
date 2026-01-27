"""Bank adapter registry."""

from __future__ import annotations

from typing import Dict, Type

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.shutterstock import ShutterstockAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.adobestock import AdobeStockAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.dreamstime import DreamstimeAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.depositphotos import DepositPhotosAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.rf123 import RF123Adapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.pond5 import Pond5Adapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.gettyimages import GettyImagesAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.bigstockphoto import BigStockPhotoAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.canstockphoto import CanStockPhotoAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.alamy import AlamyAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.pixta import PixtaAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.freepik import FreepikAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.vecteezy import VecteezyAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.storyblocks import StoryBlocksAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.envato import EnvatoAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.px500 import Px500Adapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.mostphotos import MostPhotosAdapter


BANK_ADAPTERS: Dict[str, Type[BaseBankAdapter]] = {
    "ShutterStock": ShutterstockAdapter,
    "AdobeStock": AdobeStockAdapter,
    "Dreamstime": DreamstimeAdapter,
    "DepositPhotos": DepositPhotosAdapter,
    "123RF": RF123Adapter,
    "Pond5": Pond5Adapter,
    "GettyImages": GettyImagesAdapter,
    "Alamy": AlamyAdapter,
    "BigStockPhoto": BigStockPhotoAdapter,
    "CanStockPhoto": CanStockPhotoAdapter,
    "Pixta": PixtaAdapter,
    "Freepik": FreepikAdapter,
    "Vecteezy": VecteezyAdapter,
    "StoryBlocks": StoryBlocksAdapter,
    "Envato": EnvatoAdapter,
    "500px": Px500Adapter,
    "MostPhotos": MostPhotosAdapter,
}
