"""
Unit tests for markphotomediaapprovalstatuslib/status_handler.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

from markphotomediaapprovalstatuslib import constants
from markphotomediaapprovalstatuslib.status_handler import (
    extract_status_columns,
    filter_records_by_status,
    filter_records_by_bank_status,
    find_sharpen_for_original,
    update_sharpen_status,
    is_edited_photo,
    filter_records_by_edit_type,
)


def test_extract_status_columns__case_insensitive():
    records = [{"Shutterstock Status": "x", "Other": "y"}]
    cols = extract_status_columns(records)
    assert "Shutterstock Status" in cols


def test_filter_records_by_status__selects_checked():
    records = [{"Status A": constants.STATUS_CHECKED}, {"Status A": "other"}]
    result = filter_records_by_status(records, constants.STATUS_CHECKED)
    assert result == [records[0]]


def test_filter_records_by_bank_status__matches_column():
    records = [{"Bank status": constants.STATUS_CHECKED}]
    result = filter_records_by_bank_status(records, "Bank", constants.STATUS_CHECKED)
    assert result == [records[0]]


def test_find_sharpen_for_original__finds_match():
    records = [
        {constants.COL_FILE: "photo.jpg"},
        {constants.COL_FILE: "photo_sharpen.jpg"},
    ]
    assert find_sharpen_for_original("photo.jpg", records) == records[1]


def test_update_sharpen_status__approved_sets_unused():
    original = {constants.COL_FILE: "photo.jpg", constants.COL_ORIGINAL: constants.ORIGINAL_YES}
    sharpen = {constants.COL_FILE: "photo_sharpen.jpg", "Bank status": constants.STATUS_BACKUP}
    records = [original, sharpen]

    changed = update_sharpen_status(original, records, "Bank", constants.STATUS_APPROVED)

    assert changed is True
    assert sharpen["Bank status"] == constants.STATUS_UNUSED


def test_is_edited_photo__detects_tag():
    record = {constants.COL_FILE: "photo_bw.jpg"}
    assert is_edited_photo(record) is True


def test_filter_records_by_edit_type__excludes_sharpen():
    records = [
        {constants.COL_FILE: "photo_sharpen.jpg"},
        {constants.COL_FILE: "photo.jpg"},
    ]
    filtered = filter_records_by_edit_type(records, include_edited=False)
    assert filtered == [records[1]]
