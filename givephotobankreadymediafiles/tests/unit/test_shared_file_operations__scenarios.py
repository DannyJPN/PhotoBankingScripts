"""
Unit tests for givephotobankreadymediafiles/shared/file_operations.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

import shared.file_operations as file_ops


class DummyTqdm:
    def __init__(self, iterable=None, total=None, desc=None, unit=None):
        self.iterable = iterable

    def __iter__(self):
        return iter(self.iterable or [])


@pytest.fixture
def patch_tqdm(monkeypatch):
    monkeypatch.setattr(file_ops, "tqdm", DummyTqdm)


def test_list_files__recursive(tmp_path):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "b.txt").write_text("b", encoding="utf-8")

    files = file_ops.list_files(str(tmp_path), recursive=True)

    assert any("a.txt" in f for f in files)
    assert any("b.txt" in f for f in files)


def test_copy_file__creates_dest_dir(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("x", encoding="utf-8")
    dest = tmp_path / "out" / "dest.txt"

    file_ops.copy_file(str(src), str(dest), overwrite=True)

    assert dest.exists()


def test_load_csv__header_only(tmp_path, patch_tqdm):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("A,B\n", encoding="utf-8")

    records = file_ops.load_csv(str(csv_path))

    assert records == []


def test_read_write_text(tmp_path):
    target = tmp_path / "note.txt"
    file_ops.write_text(str(target), "hello")

    assert file_ops.read_text(str(target)) == "hello"


def test_write_json_and_read_json(tmp_path):
    target = tmp_path / "data.json"
    file_ops.write_json(str(target), {"a": 1})

    assert file_ops.read_json(str(target)) == {"a": 1}
