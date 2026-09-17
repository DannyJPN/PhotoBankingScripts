"""
Unit tests for filter_prepared_media.
"""

import logging
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

from createbatchlib import constants
from createbatchlib.filtering import filter_prepared_media


def test_filter_prepared_media__filters_by_prepared_status():
    records = [
        {"Cesta": "C:/Photos/a.jpg", "Shutterstock Status": constants.PREPARED_STATUS_VALUE},
        {"Cesta": "C:/Photos/b.jpg", "Adobe Stock Status": "ne" + constants.PREPARED_STATUS_VALUE},
    ]

    result = filter_prepared_media(records, include_edited=False)

    assert result == [records[0]]


def test_filter_prepared_media__case_insensitive_status_key_and_value():
    records = [
        {"Cesta": "C:/Photos/a.jpg", "Shutterstock STATUS": constants.PREPARED_STATUS_VALUE.upper()},
    ]

    result = filter_prepared_media(records, include_edited=False)

    assert result == records


def test_filter_prepared_media__excludes_edited_when_disabled():
    records = [
        {"Cesta": "C:/Photos/upraven‚/a.jpg", "Shutterstock Status": constants.PREPARED_STATUS_VALUE},
        {"Cesta": "C:/Photos/original/b.jpg", "Shutterstock Status": constants.PREPARED_STATUS_VALUE},
    ]

    result = filter_prepared_media(records, include_edited=False)

    assert result == [records[1]]


def test_filter_prepared_media__includes_edited_when_enabled():
    records = [
        {"Cesta": "C:/Photos/upraven‚/a.jpg", "Shutterstock Status": constants.PREPARED_STATUS_VALUE},
    ]

    result = filter_prepared_media(records, include_edited=True)

    assert result == records


def test_filter_prepared_media__logs_summary(caplog):
    records = [
        {"Cesta": "C:/Photos/upraven‚/a.jpg", "Shutterstock Status": constants.PREPARED_STATUS_VALUE},
    ]

    with caplog.at_level(logging.INFO):
        filter_prepared_media(records, include_edited=False)

    assert "filtered" in caplog.text.lower()
