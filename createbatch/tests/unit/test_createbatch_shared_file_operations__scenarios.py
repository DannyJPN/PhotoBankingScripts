"""
Unit tests for createbatch/shared/file_operations.py.
"""

import csv
import os
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

import shared.file_operations as file_ops


class DummyTqdm:
    def __init__(self, iterable=None, total=None, desc=None, unit=None):
        self.iterable = iterable

    def __iter__(self):
        return iter(self.iterable or [])


@pytest.fixture
def patch_tqdm(monkeypatch):
    monkeypatch.setattr(file_ops, "tqdm", DummyTqdm)


def test_copy_file__skips_when_overwrite_false(tmp_path):
    source = tmp_path / "src.txt"
    dest = tmp_path / "dest.txt"
    source.write_text("src", encoding="utf-8")
    dest.write_text("dest", encoding="utf-8")

    file_ops.copy_file(str(source), str(dest), overwrite=False)

    assert dest.read_text(encoding="utf-8") == "dest"


def test_copy_file__creates_destination_dir(tmp_path):
    source = tmp_path / "src.txt"
    source.write_text("src", encoding="utf-8")
    dest = tmp_path / "nested" / "dest.txt"

    file_ops.copy_file(str(source), str(dest), overwrite=True)

    assert dest.exists()


def test_copy_file__raises_on_error(monkeypatch):
    monkeypatch.setattr(file_ops.shutil, "copy2", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("fail")))

    with pytest.raises(OSError):
        file_ops.copy_file("missing", "dest")


def test_ensure_directory__creates(tmp_path):
    target = tmp_path / "newdir"
    file_ops.ensure_directory(str(target))
    assert target.exists()


def test_ensure_directory__raises(monkeypatch):
    monkeypatch.setattr(file_ops.os, "makedirs", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("fail")))
    with pytest.raises(OSError):
        file_ops.ensure_directory("C:/bad/path")


def test_load_csv__header_only_returns_empty(tmp_path, patch_tqdm):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("A,B\n", encoding="utf-8")

    records = file_ops.load_csv(str(csv_path))

    assert records == []


def test_load_csv__missing_raises(patch_tqdm):
    with pytest.raises(Exception):
        file_ops.load_csv("Z:/missing.csv")


def test_save_csv__sanitizes_when_enabled(tmp_path, patch_tqdm, monkeypatch):
    records = [{"A": "=1+1", "B": "ok"}]
    output = tmp_path / "out.csv"

    called = {}

    def fake_sanitize(recs):
        called["recs"] = recs
        return [{"A": "'=1+1", "B": "ok"}]

    monkeypatch.setattr(file_ops, "sanitize_records", fake_sanitize)

    file_ops.save_csv(records, str(output), sanitize=True)

    content = output.read_text(encoding="utf-8-sig")
    assert "'=1+1" in content
    assert "A" in content
    assert called["recs"] == records


def test_save_csv__raw_when_sanitize_false(tmp_path, patch_tqdm):
    records = [{"A": "=1+1", "B": "ok"}]
    output = tmp_path / "out.csv"

    file_ops.save_csv(records, str(output), sanitize=False)

    content = output.read_text(encoding="utf-8-sig")
    assert "=1+1" in content


def test_save_csv__empty_records_warns(tmp_path, patch_tqdm, caplog):
    output = tmp_path / "out.csv"

    with caplog.at_level("WARNING"):
        file_ops.save_csv([], str(output), sanitize=True)

    assert not output.exists()
    assert "no records to save" in caplog.text.lower()
