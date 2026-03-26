"""
Unit tests for exportpreparedmedia/shared/hash_utils.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

import shared.hash_utils as hash_utils


def test_compute_file_hash__md5_fallback(monkeypatch, tmp_path, caplog):
    data_file = tmp_path / "data.bin"
    data_file.write_bytes(b"abc")

    monkeypatch.setattr(hash_utils, "XXHASH_AVAILABLE", False)
    hash_utils._xxhash_warning_logged = False

    with caplog.at_level("WARNING"):
        result = hash_utils.compute_file_hash(str(data_file), method="xxhash64")

    assert len(result) == 32
    assert "falling back to md5" in caplog.text.lower()


def test_compute_file_hash__sha256(tmp_path):
    data_file = tmp_path / "data.bin"
    data_file.write_bytes(b"abc")

    result = hash_utils.compute_file_hash(str(data_file), method="sha256")

    assert len(result) == 64
