"""
Unit tests for exportpreparedmedialib/header_mappings.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

from exportpreparedmedialib.header_mappings import HEADER_MAPPINGS


def test_header_mappings__banks_present():
    for bank in ["ShutterStock", "AdobeStock", "DreamsTime", "Pond5", "Alamy", "GettyImages"]:
        assert bank in HEADER_MAPPINGS


def test_header_mappings__required_keys():
    assert "Filename" in HEADER_MAPPINGS["ShutterStock"]
    assert "Filename" in HEADER_MAPPINGS["AdobeStock"]
