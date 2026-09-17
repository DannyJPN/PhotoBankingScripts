"""
Unit tests for markmediaascheckedlib/mark_handler.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

from markmediaascheckedlib import constants
from markmediaascheckedlib.mark_handler import (
    extract_status_columns,
    filter_ready_records,
    update_statuses,
    is_edited_photo,
    filter_records_by_edit_type,
    filter_status_columns,
    parse_banks,
)


def test_extract_status_columns__case_insensitive():
    records = [{"Shutterstock Status": "x", "Other": "y"}]
    cols = extract_status_columns(records)
    assert "Shutterstock Status" in cols


def test_filter_ready_records__selects_ready():
    records = [
        {"Status A": constants.STATUS_READY},
        {"Status A": "other"},
    ]
    ready = filter_ready_records(records, ["Status A"])
    assert ready == [records[0]]


def test_update_statuses__replaces_ready():
    records = [{"Status A": constants.STATUS_READY}]
    count = update_statuses(records, ["Status A"])
    assert count == 1
    assert records[0]["Status A"] == constants.STATUS_CHECKED


def test_is_edited_photo__detects_tag():
    record = {constants.COL_FILE: "photo_bw.jpg"}
    assert is_edited_photo(record) is True


def test_filter_records_by_edit_type__excludes_edited():
    records = [
        {constants.COL_FILE: "photo_bw.jpg"},
        {constants.COL_FILE: "photo.jpg"},
    ]
    filtered = filter_records_by_edit_type(records, include_edited=False)
    assert filtered == [records[1]]


def test_filter_status_columns__matches_case_insensitively():
    filtered = filter_status_columns(
        ["AdobeStock status", "GettyImages status"],
        ["adobestock"],
    )

    assert filtered == ["AdobeStock status"]


def test_filter_status_columns__unknown_bank__logs_warning_and_returns_empty(caplog):
    with caplog.at_level("WARNING"):
        filtered = filter_status_columns(
            ["AdobeStock status", "GettyImages status"],
            ["NonExistentBank"],
        )

    assert filtered == []
    assert "NonExistentBank" in caplog.text


def test_filter_status_columns__empty_banks_list_returns_no_columns():
    filtered = filter_status_columns(
        ["AdobeStock status", "GettyImages status"],
        [],
    )

    assert filtered == []


def test_filter_status_columns__repeated_bank_is_deduplicated():
    filtered = filter_status_columns(
        ["AdobeStock status", "GettyImages status"],
        ["adobestock", "AdobeStock"],
    )

    assert filtered == ["AdobeStock status"]


def test_parse_banks__splits_and_strips_names():
    assert parse_banks("AdobeStock,ShutterStock") == ["AdobeStock", "ShutterStock"]


def test_parse_banks__ignores_whitespace_and_empty_items():
    assert parse_banks(" AdobeStock , ,ShutterStock,") == ["AdobeStock", "ShutterStock"]


def test_parse_banks__whitespace_or_comma_only_value_returns_empty_list():
    assert parse_banks(",") == []
    assert parse_banks("   ") == []
