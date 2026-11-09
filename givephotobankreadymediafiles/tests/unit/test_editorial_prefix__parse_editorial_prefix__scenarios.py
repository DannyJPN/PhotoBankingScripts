"""
Unit tests for givephotobankreadymediafileslib/editorial_prefix.py.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib.editorial_prefix import (
    extract_editorial_data,
    has_editorial_prefix_for_city,
    parse_editorial_prefix,
)


@pytest.mark.parametrize(
    "description, expected",
    [
        ("Prague, Czech - 15 03 2024: Old town", {"city": "Prague", "country": "Czech", "date": "15 03 2024"}),
        ("Frydek-Mistek, Czech - 12 14 2014: Sky", {"city": "Frydek-Mistek", "country": "Czech", "date": "12 14 2014"}),
        (
            "Frenstat pod Radhostem, Czech - 01 02 2020: Square",
            {"city": "Frenstat pod Radhostem", "country": "Czech", "date": "01 02 2020"},
        ),
        (
            "CESKY KRUMLOV, CZECH - 01 02 2020: Castle",
            {"city": "CESKY KRUMLOV", "country": "CZECH", "date": "01 02 2020"},
        ),
    ],
)
def test_editorial_prefix__parse_editorial_prefix__valid_prefixes(description: str, expected: Dict[str, str]) -> None:
    assert parse_editorial_prefix(description) == expected


@pytest.mark.parametrize(
    "description",
    [
        "",
        None,
        "Beautiful evening sky above Prague",
        "Grey shaded - Frydek-Mistek, Czech - 12 14 2014: Sky",
        "Frýdek-Místek, Czech - 12 14 2014: Sky",
        "Prague, Czech Republic - 15 03 2024: Old town",
        "Prague, Czech - 2024-03-15: Old town",
        " Prague, Czech - 15 03 2024: leading space",
        "Cesky  Krumlov, Czech - 15 03 2024: double space",
        "Frydek--Mistek, Czech - 15 03 2024: double hyphen",
    ],
)
def test_editorial_prefix__parse_editorial_prefix__no_prefix_returns_none(description: Optional[str]) -> None:
    assert parse_editorial_prefix(description) is None


def test_editorial_prefix__extract_editorial_data__returns_parsed_data(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        data = extract_editorial_data("Ostrava, Czech - 01 02 2020: Mine", "DSC0001.JPG")
    assert data == {"city": "Ostrava", "country": "Czech", "date": "01 02 2020"}
    assert not caplog.records


def test_editorial_prefix__extract_editorial_data__missing_prefix_warns_with_file_name(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        data = extract_editorial_data("Grey shaded - Ostrava, Czech - 01 02 2020: Mine", "DSC0001_bw.JPG")
    assert data is None
    assert any("DSC0001_bw.JPG" in record.getMessage() for record in caplog.records)


@pytest.mark.parametrize(
    "description, city, country, expected",
    [
        ("OLOMOUC, CZECH - 01 02 2020: Square", "Olomouc", "Czech", True),
        ("Frydek-Mistek, Czech - 01 02 2020: Sky", "frydek-mistek", "Czech", True),
        ("Olomouc, Czech - 01 02 2020: Square", "Ostrava", "Czech", False),
        ("Olomouc, Slovakia - 01 02 2020: Square", "Olomouc", "Czech", False),
        ("Square in Olomouc", "Olomouc", "Czech", False),
        (None, "Olomouc", "Czech", False),
        ("Frýdek-Místek, Czech - 01 02 2020: Sky", "Frýdek-Místek", "Czech", True),
        ("STARÉ HAMRY, CZECH - 01 02 2020: Hills", "Staré Hamry", "Czech", True),
        ("Frýdek-Místek, Czech - 01 02 2020: Sky", "Frydek-Mistek", "Czech", False),
        ("Olomouc, Czech - 01 02 2020: Square", "", "Czech", False),
    ],
)
def test_editorial_prefix__has_editorial_prefix_for_city__matches_city_and_country(
    description: Optional[str], city: str, country: str, expected: bool
) -> None:
    assert has_editorial_prefix_for_city(description, city, country) is expected
