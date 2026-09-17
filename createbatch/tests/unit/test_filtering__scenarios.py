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
from createbatchlib.filtering import filter_prepared_media, is_editorial_record, filter_editorial_for_bank


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
        {"Cesta": "C:/Photos/upravené/a.jpg", "Shutterstock Status": constants.PREPARED_STATUS_VALUE},
        {"Cesta": "C:/Photos/original/b.jpg", "Shutterstock Status": constants.PREPARED_STATUS_VALUE},
    ]

    result = filter_prepared_media(records, include_edited=False)

    assert result == [records[1]]


def test_filter_prepared_media__includes_edited_when_enabled():
    records = [
        {"Cesta": "C:/Photos/upravené/a.jpg", "Shutterstock Status": constants.PREPARED_STATUS_VALUE},
    ]

    result = filter_prepared_media(records, include_edited=True)

    assert result == records


def test_filter_prepared_media__logs_summary(caplog):
    records = [
        {"Cesta": "C:/Photos/upravené/a.jpg", "Shutterstock Status": constants.PREPARED_STATUS_VALUE},
    ]

    with caplog.at_level(logging.INFO):
        filter_prepared_media(records, include_edited=False)

    assert "filtered" in caplog.text.lower()


def test_is_editorial_record__single_word_city_in_desc():
    record = {"Název": "", "Popis": "Prague, Czechia - 01 02 2020: Some event"}
    assert is_editorial_record(record) is True


def test_is_editorial_record__multiword_city_in_desc():
    record = {"Název": "", "Popis": "STARE HAMRY, CZECH - 05 07 2018: Stone plaque on wall"}
    assert is_editorial_record(record) is True


def test_is_editorial_record__multiword_city_three_words():
    record = {"Název": "", "Popis": "KARLOVA STUDANKA, CZECH - 15 08 2017: Forest spa resort"}
    assert is_editorial_record(record) is True


def test_is_editorial_record__non_editorial_desc():
    record = {"Název": "Mountain lake at sunset", "Popis": "Beautiful alpine scenery"}
    assert is_editorial_record(record) is False


def test_filter_editorial_for_bank__removes_multiword_city_from_no_editorial_bank():
    records = [
        {"Název": "", "Popis": "STARE HAMRY, CZECH - 05 07 2018: Stone plaque"},
        {"Název": "", "Popis": "Beautiful mountain landscape"},
    ]
    result = filter_editorial_for_bank(records, "AdobeStock")
    assert len(result) == 1
    assert "landscape" in result[0]["Popis"]


def test_filter_editorial_for_bank__keeps_multiword_city_for_editorial_bank():
    records = [
        {"Název": "", "Popis": "STARE HAMRY, CZECH - 05 07 2018: Stone plaque"},
    ]
    result = filter_editorial_for_bank(records, "ShutterStock")
    assert len(result) == 1
