"""
Unit tests for exportpreparedmedia/shared/file_operations.py.
"""

import os
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

import shared.file_operations as file_ops


class DummyTqdm:
    def __init__(self, iterable=None, total=None, desc=None, unit=None):
        self.iterable = iterable

    def __iter__(self):
        return iter(self.iterable or [])


@pytest.fixture
def patch_tqdm(monkeypatch):
    monkeypatch.setattr(file_ops, "tqdm", DummyTqdm)


def test_list_files__recursive_and_non_recursive(tmp_path):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "b.txt").write_text("b", encoding="utf-8")

    all_files = file_ops.list_files(str(tmp_path), recursive=True)
    top_files = file_ops.list_files(str(tmp_path), recursive=False)

    assert any("a.txt" in p for p in all_files)
    assert any("b.txt" in p for p in all_files)
    assert any("a.txt" in p for p in top_files)
    assert not any("b.txt" in p for p in top_files)


def test_copy_file__creates_dest_dir(tmp_path):
    source = tmp_path / "src.txt"
    source.write_text("data", encoding="utf-8")
    dest = tmp_path / "out" / "dest.txt"

    file_ops.copy_file(str(source), str(dest), overwrite=True)

    assert dest.exists()


def test_move_file__skips_when_dest_exists(tmp_path):
    source = tmp_path / "src.txt"
    source.write_text("src", encoding="utf-8")
    dest = tmp_path / "dest.txt"
    dest.write_text("dest", encoding="utf-8")

    file_ops.move_file(str(source), str(dest), overwrite=False)

    assert dest.read_text(encoding="utf-8") == "dest"
    assert source.exists()


def test_ensure_directory__creates(tmp_path):
    target = tmp_path / "newdir"
    file_ops.ensure_directory(str(target))
    assert target.exists()


def test_load_csv__header_only(tmp_path, patch_tqdm):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("A,B\n", encoding="utf-8")

    records = file_ops.load_csv(str(csv_path))

    assert records == []


def test_save_csv__sanitizes_when_enabled(tmp_path, patch_tqdm, monkeypatch):
    records = [{"A": "=1+1"}]
    output = tmp_path / "out.csv"

    monkeypatch.setattr(file_ops, "sanitize_records", lambda _r: [{"A": "'=1+1"}])

    file_ops.save_csv(records, str(output), sanitize=True)

    content = output.read_text(encoding="utf-8-sig")
    assert "'=1+1" in content


def test_save_csv__empty_records_warns(tmp_path, patch_tqdm, caplog):
    output = tmp_path / "out.csv"

    with caplog.at_level("WARNING"):
        file_ops.save_csv([], str(output), sanitize=True)

    assert not output.exists()
    assert "no records to save" in caplog.text.lower()


def test_get_hash_map_from_folder__uses_compute(monkeypatch, tmp_path, patch_tqdm):
    file_a = tmp_path / "a.txt"
    file_a.write_text("a", encoding="utf-8")

    monkeypatch.setattr(file_ops, "compute_file_hash", lambda _p: "hash")

    result = file_ops.get_hash_map_from_folder(str(tmp_path), pattern="a.txt", recursive=False)

    assert result[str(file_a)] == "hash"


def test_unify_duplicate_files__renames_to_shortest(tmp_path, patch_tqdm, monkeypatch):
    file_short = tmp_path / "a.txt"
    file_long = tmp_path / "longname.txt"
    file_short.write_text("data", encoding="utf-8")
    file_long.write_text("data", encoding="utf-8")

    monkeypatch.setattr(file_ops, "compute_file_hash", lambda _p: "hash")

    file_ops.unify_duplicate_files(str(tmp_path), recursive=False)

    assert (tmp_path / "a.txt").exists()
    assert not file_long.exists()
