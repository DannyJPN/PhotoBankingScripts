"""
Unit tests for givephotobankreadymediafiles/shared/csv_sanitizer.py.
"""

import sys
from pathlib import Path
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.csv_sanitizer import sanitize_field, sanitize_record, sanitize_records, is_dangerous


class TestSanitizeField:
    def test_normal_text_unchanged(self):
        value = "Normal text"
        assert sanitize_field(value) == value
        assert not is_dangerous(value)

    def test_none_and_empty(self):
        assert sanitize_field(None) == ""
        assert sanitize_field("") == ""
        assert sanitize_field("   ") == ""

    def test_non_string(self):
        assert sanitize_field(123) == "123"

    @pytest.mark.parametrize("value", ["=1+1", "+SUM(1+1)", "-1+1", "@SUM(1)"])
    def test_dangerous_prefixes(self, value):
        assert sanitize_field(value).startswith("'")
        assert is_dangerous(value)

    @pytest.mark.parametrize("value", ["\tTAB", "\nNL", "\rCR"])
    def test_control_prefixes(self, value):
        assert sanitize_field(value).startswith("'")
        assert is_dangerous(value)

    def test_suspicious_patterns(self):
        values = ["cmd|'/c calc'", "file:///c:/windows", "\\\\server\\share"]
        for v in values:
            assert sanitize_field(v).startswith("'")
            assert is_dangerous(v)

    def test_leading_single_quote_not_doubled(self):
        value = "'=SUM(1+1)"
        assert sanitize_field(value) == "'=SUM(1+1)"

    def test_legit_url_not_sanitized(self):
        value = "https://example.com/path"
        assert sanitize_field(value) == value

    def test_hyphen_mid_text_not_sanitized(self):
        value = "High-quality photo (2024)"
        assert sanitize_field(value) == value
        assert not is_dangerous(value)


class TestSanitizeRecords:
    def test_sanitize_record(self):
        record = {"name": "=cmd|calc", "desc": "Normal"}
        result = sanitize_record(record)
        assert result["name"].startswith("'")
        assert result["desc"] == "Normal"

    def test_sanitize_records_list(self):
        records = [{"a": "=1"}, {"a": "ok"}]
        result = sanitize_records(records)
        assert result[0]["a"].startswith("'")
        assert result[1]["a"] == "ok"

    def test_empty_records(self):
        assert sanitize_records([]) == []
