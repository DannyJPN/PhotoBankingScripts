"""
Unit tests for exportpreparedmedialib/constants.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

from exportpreparedmedialib import constants


def test_constants__types_and_names():
    assert isinstance(constants.DEFAULT_PHOTO_CSV, str)
    assert isinstance(constants.DEFAULT_OUTPUT_DIR, str)
    assert isinstance(constants.DEFAULT_OUTPUT_PREFIX, str)
    assert isinstance(constants.PHOTOBANKS, list)


def test_constants__jpg_supported():
    for bank, formats in constants.PHOTOBANK_SUPPORTED_FORMATS.items():
        assert ".jpg" in formats, f"{bank} should support .jpg"


def test_constants__export_formats_override():
    assert "DreamsTime" in constants.PHOTOBANK_EXPORT_FORMATS
