"""
Unit tests for exportpreparedmedia/shared/csv_sanitizer.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

from shared.csv_sanitizer import sanitize_field, sanitize_record, sanitize_records, is_dangerous


def test_sanitize_field__basic():
    assert sanitize_field("text") == "text"
    assert sanitize_field("") == ""
    assert sanitize_field(None) == ""
    assert sanitize_field(123) == "123"


def test_sanitize_field__dangerous():
    assert sanitize_field("=1+1") == "'=1+1"
    assert sanitize_field("+1+1") == "'+1+1"
    assert sanitize_field("cmd|calc") == "'cmd|calc"


def test_sanitize_record_and_records():
    record = {"a": "=1+1", "b": "ok"}
    assert sanitize_record(record)["a"].startswith("'")
    assert sanitize_records([record])[0]["b"] == "ok"


def test_is_dangerous():
    assert is_dangerous("=1+1") is True
    assert is_dangerous("normal") is False
