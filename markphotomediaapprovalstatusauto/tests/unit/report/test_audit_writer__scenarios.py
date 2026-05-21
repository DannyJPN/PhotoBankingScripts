"""Unit tests for audit_writer.py."""

import csv
import os
import tempfile

from markphotomediaapprovalstatusautolib.report.audit_models import AuditEntry
from markphotomediaapprovalstatusautolib.report.audit_writer import AuditWriter


def _make_entry(**kwargs) -> AuditEntry:
    defaults = dict(
        timestamp="2026-01-01T00:00:00",
        local_file="DSC00001.JPG",
        bank="TestBank",
        result="NOT_FOUND",
        candidate_url=None,
        candidate_id=None,
        contributor_match=None,
        phash_distance=None,
        dhash_distance=None,
        dimension_match=None,
        preview_url=None,
        reason="no_candidates",
    )
    defaults.update(kwargs)
    return AuditEntry(**defaults)


def test_audit_writer__creates_file_with_header():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "audit.csv")
        AuditWriter(path).write(_make_entry())
        assert os.path.exists(path)
        with open(path, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 1
        assert rows[0]["local_file"] == "DSC00001.JPG"


def test_audit_writer__found_entry_written_correctly():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "audit.csv")
        AuditWriter(path).write(
            _make_entry(result="FOUND", candidate_url="http://example.com/img", phash_distance=1, contributor_match=True, reason="phash:1")
        )
        with open(path, encoding="utf-8") as fh:
            row = next(csv.DictReader(fh))
        assert row["result"] == "FOUND"
        assert row["phash_distance"] == "1"
        assert row["contributor_match"] == "True"


def test_audit_writer__appends_multiple_entries():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "audit.csv")
        w = AuditWriter(path)
        w.write(_make_entry(local_file="A.JPG"))
        w.write(_make_entry(local_file="B.JPG"))
        with open(path, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 2
        assert rows[0]["local_file"] == "A.JPG"
        assert rows[1]["local_file"] == "B.JPG"


def test_audit_writer__none_fields_written_as_empty_string():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "audit.csv")
        AuditWriter(path).write(_make_entry())
        with open(path, encoding="utf-8") as fh:
            row = next(csv.DictReader(fh))
        assert row["phash_distance"] == ""
        assert row["candidate_url"] == ""
        assert row["contributor_match"] == ""