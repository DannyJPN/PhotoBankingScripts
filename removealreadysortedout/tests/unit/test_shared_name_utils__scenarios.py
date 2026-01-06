"""
Unit tests for removealreadysortedout/shared/name_utils.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

import shared.name_utils as name_utils


def test_extract_numeric_suffix():
    assert name_utils.extract_numeric_suffix("PICT0012.jpg") == 12
    assert name_utils.extract_numeric_suffix("NOPE.jpg") is None


def test_generate_indexed_filename():
    assert name_utils.generate_indexed_filename(3, ".jpg") == "PICT0003.jpg"


def test_generate_indexed_filename__invalid():
    try:
        name_utils.generate_indexed_filename(0, ".jpg")
    except ValueError as exc:
        assert "must be positive" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_find_next_available_number():
    assert name_utils.find_next_available_number({1, 2, 3}, max_number=5) == 4
