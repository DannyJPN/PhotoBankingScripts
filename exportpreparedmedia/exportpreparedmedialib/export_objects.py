# File: exportpreparedmedialib/export_objects.py

import logging
from exportpreparedmedialib.header_mappings import HEADER_MAPPINGS

class BaseExport:
    def __init__(self, photobank, **kwargs):
        logging.debug(f"Creating BaseExport object for {photobank}")
        self.photobank = photobank
        self.fields = kwargs

    def to_dict(self):
        header_mapping = HEADER_MAPPINGS.get(self.photobank, {})
        return {header_mapping.get(k, k): v for k, v in self.fields.items()}

class ShutterStockExport(BaseExport):
    def __init__(self, **kwargs):
        super().__init__("ShutterStock", **kwargs)

class AdobeStockExport(BaseExport):
    def __init__(self, **kwargs):
        super().__init__("AdobeStock", **kwargs)

class DreamstimeExport(BaseExport):
    def __init__(self, **kwargs):
        super().__init__("Dreamstime", **kwargs)

class DepositPhotosExport(BaseExport):
    def __init__(self, **kwargs):
        super().__init__("DepositPhotos", **kwargs)

class BigStockPhotoExport(BaseExport):
    def __init__(self, **kwargs):
        super().__init__("BigStockPhoto", **kwargs)

class RF123Export(BaseExport):
    def __init__(self, **kwargs):
        super().__init__("123RF", **kwargs)

class CanStockPhotoExport(BaseExport):
    def __init__(self, **kwargs):
        super().__init__("CanStockPhoto", **kwargs)

class Pond5Export(BaseExport):
    def __init__(self, **kwargs):
        super().__init__("Pond5", **kwargs)

class AlamyExport(BaseExport):
    def __init__(self, **kwargs):
        super().__init__("Alamy", **kwargs)

class GettyImagesExport(BaseExport):
    def __init__(self, **kwargs):
        super().__init__("GettyImages", **kwargs)
