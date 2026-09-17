"""
Unit tests for pullnewmediatounsorted/shared/name_utils.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "pullnewmediatounsorted"
sys.path.insert(0, str(package_root))

from shared.name_utils import extract_numeric_suffix, generate_indexed_filename, find_next_available_number


def test_extract_numeric_suffix__matches_prefix():
    assert extract_numeric_suffix("PICT0001.jpg", prefix="PICT") == 1
    assert extract_numeric_suffix("OTHER0001.jpg", prefix="PICT") is None


def test_generate_indexed_filename__formats():
    assert generate_indexed_filename(12, ".jpg", prefix="PICT", width=4) == "PICT0012.jpg"


def test_find_next_available_number__returns_first_free():
    assert find_next_available_number({1, 2, 3}, max_number=5) == 4
