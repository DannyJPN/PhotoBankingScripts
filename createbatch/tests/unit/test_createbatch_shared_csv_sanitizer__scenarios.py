"""
Unit tests for createbatch/shared/csv_sanitizer.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

from shared.csv_sanitizer import sanitize_field, sanitize_record, sanitize_records, is_dangerous


def test_sanitize_field__basic_cases():
    assert sanitize_field("hello") == "hello"
    assert sanitize_field("") == ""
    assert sanitize_field(None) == ""
    assert sanitize_field(123) == "123"


def test_sanitize_field__dangerous_prefixes():
    assert sanitize_field("=SUM(1,1)") == "'=SUM(1,1)"
    assert sanitize_field("+SUM(1,1)") == "'+SUM(1,1)"
    assert sanitize_field("-SUM(1,1)") == "'-SUM(1,1)"
    assert sanitize_field("@SUM(1,1)") == "'@SUM(1,1)"


def test_sanitize_field__suspicious_patterns():
    assert sanitize_field("cmd|calc") == "'cmd|calc"
    assert sanitize_field("file:///etc/passwd") == "'file:///etc/passwd"
    assert sanitize_field(r"\\server\share") == "'\\server\\share"


def test_sanitize_field__leading_quote_normalized():
    assert sanitize_field("'=SUM(1,1)") == "'=SUM(1,1)"


def test_sanitize_record_and_records():
    record = {"a": "=1+1", "b": "safe"}
    sanitized = sanitize_record(record)
    assert sanitized["a"].startswith("'")
    assert sanitized["b"] == "safe"

    records = [record, {"a": "ok"}]
    sanitized_records = sanitize_records(records)
    assert len(sanitized_records) == 2


def test_is_dangerous():
    assert is_dangerous("=SUM(1,1)") is True
    assert is_dangerous("normal") is False
    assert is_dangerous("") is False
