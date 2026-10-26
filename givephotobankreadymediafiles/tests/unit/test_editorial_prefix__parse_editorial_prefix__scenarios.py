"""
Unit tests for givephotobankreadymediafileslib/editorial_prefix.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib.editorial_prefix import parse_editorial_prefix


@pytest.mark.parametrize(
    "description, expected",
    [
        ("Prague, Czech - 15 03 2024: Old town", {"city": "Prague", "country": "Czech", "date": "15 03 2024"}),
        ("Frydek-Mistek, Czech - 12 14 2014: Sky", {"city": "Frydek-Mistek", "country": "Czech", "date": "12 14 2014"}),
        ("Frenstat pod Radhostem, Czech - 01 02 2020: Square",
         {"city": "Frenstat pod Radhostem", "country": "Czech", "date": "01 02 2020"}),
        ("CESKY KRUMLOV, CZECH - 01 02 2020: Castle", {"city": "CESKY KRUMLOV", "country": "CZECH", "date": "01 02 2020"}),
    ],
)
def test_parse_editorial_prefix__valid_prefixes(description, expected):
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
    ],
)
def test_parse_editorial_prefix__no_prefix_returns_none(description):
    assert parse_editorial_prefix(description) is None
