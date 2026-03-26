"""
Unit tests for exportpreparedmedia/shared/media_filter.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

from shared.media_filter import filter_prepared_items


def test_filter_prepared_items__matches_status():
    items = [
        {"Status": "ready"},
        {"Other": "x"},
        {"status": "ready"},
    ]

    result = filter_prepared_items(items, "ready")

    assert result == [items[0], items[2]]


def test_filter_prepared_items__error_returns_empty():
    result = filter_prepared_items(None, "ready")
    assert result == []
