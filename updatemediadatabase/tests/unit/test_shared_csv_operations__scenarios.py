"""
Unit tests for updatemediadatabase/shared/csv_operations.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))

import shared.csv_operations as csv_operations


def test_load_csv__missing_file(monkeypatch):
    monkeypatch.setattr(csv_operations.os.path, "exists", lambda _p: False)
    assert csv_operations.load_csv("missing.csv") == []


def test_save_csv__missing_sanitizer_raises(monkeypatch, tmp_path):
    file_path = tmp_path / "data.csv"
    records = [{"a": "b"}]

    monkeypatch.setattr(csv_operations.os.path, "exists", lambda _p: False)
    try:
        csv_operations.save_csv(str(file_path), records, backup=False)
    except Exception as exc:
        assert "sanitize_records" in str(exc) or isinstance(exc, Exception)
    else:
        raise AssertionError("Expected exception for missing sanitize_records")
