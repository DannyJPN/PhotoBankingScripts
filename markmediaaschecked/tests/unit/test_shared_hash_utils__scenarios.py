"""
Unit tests for markmediaaschecked/shared/hash_utils.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

import shared.hash_utils as hash_utils


def test_compute_file_hash__md5(tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("abc", encoding="utf-8")

    result = hash_utils.compute_file_hash(str(file_path), method="md5")
    assert len(result) == 32


def test_compute_file_hash__xxhash_fallback(monkeypatch, tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("abc", encoding="utf-8")

    monkeypatch.setattr(hash_utils, "XXHASH_AVAILABLE", False)
    hash_utils._xxhash_warning_logged = False

    result = hash_utils.compute_file_hash(str(file_path), method="xxhash64")
    assert len(result) == 32
