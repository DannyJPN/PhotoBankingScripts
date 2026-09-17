"""
Unit tests for createbatchlib.constants values.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

from createbatchlib import constants


def test_constants__expected_types():
    assert isinstance(constants.DEFAULT_PHOTO_CSV_FILE, str)
    assert isinstance(constants.DEFAULT_PROCESSED_MEDIA_FOLDER, str)
    assert isinstance(constants.DEFAULT_LOG_DIR, str)
    assert isinstance(constants.STATUS_FIELD_KEYWORD, str)
    assert isinstance(constants.PREPARED_STATUS_VALUE, str)
    assert isinstance(constants.RAW_FORMATS, set)
    assert isinstance(constants.PHOTOBANK_SUPPORTED_FORMATS, dict)
    assert isinstance(constants.FORMAT_SUBDIRS, dict)
    assert isinstance(constants.PHOTOBANK_BATCH_SIZE_LIMITS, dict)


def test_constants__jpg_supported_by_all_banks():
    for bank, formats in constants.PHOTOBANK_SUPPORTED_FORMATS.items():
        assert ".jpg" in formats, f"{bank} should support .jpg"


def test_constants__format_subdirs_include_raw_formats():
    for ext in constants.RAW_FORMATS:
        assert constants.FORMAT_SUBDIRS.get(ext) == "raw"
