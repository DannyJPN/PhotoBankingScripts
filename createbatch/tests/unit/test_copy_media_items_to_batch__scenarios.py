"""
Unit tests for copy_media_items_to_batch.
"""

import os
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

from createbatchlib.copy_media_items_to_batch import copy_media_items_to_batch
import createbatchlib.copy_media_items_to_batch as copy_module


class DummyTqdm:
    def __init__(self, total, desc, unit):
        self.total = total
        self.desc = desc
        self.unit = unit
        self.updates = 0

    def update(self, count):
        self.updates += count

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def patch_tqdm(monkeypatch):
    monkeypatch.setattr(copy_module, "tqdm", DummyTqdm)


def test_copy_media_items_to_batch__copies_and_updates_path(tmp_path, patch_tqdm):
    source = tmp_path / "src.jpg"
    source.write_text("data", encoding="utf-8")
    dest_root = tmp_path / "out"
    dest_root.mkdir()

    items = [{"Cesta": str(source)}]
    result = copy_media_items_to_batch(items, str(dest_root))

    dest_path = dest_root / source.name
    assert dest_path.exists()
    assert result[0]["Cesta"] == str(dest_path)


def test_copy_media_items_to_batch__skips_existing_destination(tmp_path, patch_tqdm):
    source = tmp_path / "src.jpg"
    source.write_text("source", encoding="utf-8")
    dest_root = tmp_path / "out"
    dest_root.mkdir()
    dest_path = dest_root / source.name
    dest_path.write_text("dest", encoding="utf-8")

    items = [{"Cesta": str(source)}]
    result = copy_media_items_to_batch(items, str(dest_root))

    assert dest_path.read_text(encoding="utf-8") == "dest"
    assert result[0]["Cesta"] == str(dest_path)


def test_copy_media_items_to_batch__source_metadata_error_logs(tmp_path, patch_tqdm, monkeypatch, caplog):
    source = tmp_path / "src.jpg"
    source.write_text("data", encoding="utf-8")
    dest_root = tmp_path / "out"
    dest_root.mkdir()

    original_stat = os.stat
    calls = {"count": 0}

    def flaky_stat(path):
        if str(path) == str(source) and calls["count"] == 0:
            calls["count"] += 1
            raise OSError("stat failed")
        return original_stat(path)

    monkeypatch.setattr(copy_module.os, "stat", flaky_stat)

    items = [{"Cesta": str(source)}]
    with caplog.at_level("ERROR"):
        copy_media_items_to_batch(items, str(dest_root))

    assert "error retrieving source file metadata" in caplog.text.lower()


def test_copy_media_items_to_batch__utime_error_logs(tmp_path, patch_tqdm, monkeypatch, caplog):
    source = tmp_path / "src.jpg"
    source.write_text("data", encoding="utf-8")
    dest_root = tmp_path / "out"
    dest_root.mkdir()

    def fail_utime(_path, _times):
        raise OSError("utime failed")

    monkeypatch.setattr(copy_module.os, "utime", fail_utime)

    items = [{"Cesta": str(source)}]
    with caplog.at_level("ERROR"):
        copy_media_items_to_batch(items, str(dest_root))

    assert "error setting timestamps" in caplog.text.lower()


def test_copy_media_items_to_batch__copy_failure_exits(tmp_path, patch_tqdm, monkeypatch):
    source = tmp_path / "src.jpg"
    source.write_text("data", encoding="utf-8")
    dest_root = tmp_path / "out"
    dest_root.mkdir()

    def fail_copy(_src, _dst):
        raise OSError("copy failed")

    monkeypatch.setattr(copy_module.shutil, "copy2", fail_copy)

    items = [{"Cesta": str(source)}]
    with pytest.raises(SystemExit) as excinfo:
        copy_media_items_to_batch(items, str(dest_root))

    assert excinfo.value.code == 1
