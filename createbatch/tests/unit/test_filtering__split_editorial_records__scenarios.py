"""
Unit tests for split_editorial_records.
"""

import logging
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(createbatch_root))

from createbatchlib.filtering import split_editorial_records

EDITORIAL = {"Název": "Ostrava, Czech - 07 05 2021: Statue", "Popis": ""}
EDITORIAL_MULTI_WORD = {"Název": "", "Popis": "Frenstat pod Radhostem, Czech - 08 07 2022: Square"}
COMMERCIAL = {"Název": "Yellow flower", "Popis": "Close-up of a flower"}


def test_split_editorial_records__splits_for_bank_accepting_editorial():
    records = [COMMERCIAL, EDITORIAL, EDITORIAL_MULTI_WORD]

    commercial, editorial = split_editorial_records(records, "Pond5")

    assert commercial == [COMMERCIAL]
    assert editorial == [EDITORIAL, EDITORIAL_MULTI_WORD]


def test_split_editorial_records__drops_editorial_for_bank_without_editorial(caplog):
    with caplog.at_level(logging.INFO):
        commercial, editorial = split_editorial_records([EDITORIAL, COMMERCIAL], "AdobeStock")

    assert commercial == [COMMERCIAL]
    assert editorial == []
    assert "Filtered out 1 editorial records for AdobeStock" in caplog.text


def test_split_editorial_records__empty_input():
    assert split_editorial_records([], "Pond5") == ([], [])


def test_split_editorial_records__only_commercial_logs_nothing(caplog):
    with caplog.at_level(logging.INFO):
        commercial, editorial = split_editorial_records([COMMERCIAL], "Pond5")

    assert commercial == [COMMERCIAL]
    assert editorial == []
    assert "editorial" not in caplog.text
