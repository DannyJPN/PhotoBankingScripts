"""
Unit tests for exportpreparedmedialib/column_maps.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

from exportpreparedmedialib.column_maps import (
    editorial_to_numeric,
    get_super_tags,
    check_people,
    check_property,
    license_type_from_editorial,
    get_column_map,
)


def test_editorial_to_numeric():
    assert editorial_to_numeric("yes") == "1"
    assert editorial_to_numeric("no") == "0"


def test_get_super_tags():
    assert get_super_tags("a,b,c") == "a,b,c"
    assert get_super_tags("") == ""


def test_check_people():
    assert check_people("people on street") == "crowd"
    assert check_people("no one") == "0"


def test_check_property():
    assert check_property("house exterior") == "Y"
    assert check_property("trees") == "N"


def test_license_type_from_editorial():
    assert license_type_from_editorial("yes") == "RF-E"
    assert license_type_from_editorial("no") == "RF"


def test_get_column_map__unknown_returns_empty():
    assert get_column_map("Unknown") == []
