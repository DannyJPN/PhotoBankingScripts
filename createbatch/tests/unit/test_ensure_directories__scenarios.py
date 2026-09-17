"""
Unit tests for ensure_directories.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

from createbatchlib.ensure_directories import ensure_directories
import createbatchlib.ensure_directories as ensure_module


class DummyTqdm:
    def __init__(self, total, desc, unit):
        self.total = total
        self.desc = desc
        self.unit = unit

    def update(self, _count):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def patch_tqdm(monkeypatch):
    monkeypatch.setattr(ensure_module, "tqdm", DummyTqdm)


def test_ensure_directories__creates_missing_dirs(tmp_path, patch_tqdm):
    out_dir = tmp_path / "out"
    log_dir = tmp_path / "logs"

    ensure_directories(str(out_dir), str(log_dir))

    assert out_dir.exists()
    assert log_dir.exists()


def test_ensure_directories__existing_dirs_ok(tmp_path, patch_tqdm):
    out_dir = tmp_path / "out"
    log_dir = tmp_path / "logs"
    out_dir.mkdir()
    log_dir.mkdir()

    ensure_directories(str(out_dir), str(log_dir))

    assert out_dir.exists()
    assert log_dir.exists()


def test_ensure_directories__error_exits(tmp_path, patch_tqdm, monkeypatch):
    out_dir = tmp_path / "out"
    log_dir = tmp_path / "logs"

    def fail_makedirs(_path):
        raise OSError("no permission")

    monkeypatch.setattr(ensure_module.os, "makedirs", fail_makedirs)

    with pytest.raises(SystemExit) as excinfo:
        ensure_directories(str(out_dir), str(log_dir))

    assert excinfo.value.code == 1
