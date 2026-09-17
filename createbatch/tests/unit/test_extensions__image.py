"""
Unit tests for image extensions list.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

from createbatchlib.image_extensions import IMAGE_EXTENSIONS


def test_image_extensions__expected_values():
    assert isinstance(IMAGE_EXTENSIONS, list)
    for ext in ["jpg", "jpeg", "png", "tiff", "tif", "raw", "nef", "dng"]:
        assert ext in IMAGE_EXTENSIONS
