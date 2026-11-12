"""
Unit tests for removealreadysortedout/shared/file_operations.py.
"""

from __future__ import annotations

import errno
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

import shared.file_operations as file_operations


def test_list_files__non_recursive(tmp_path):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.log").write_text("b", encoding="utf-8")

    files = file_operations.list_files(str(tmp_path), pattern="\\.txt$", recursive=False)
    assert any(path.endswith("a.txt") for path in files)
    assert all("b.log" not in path for path in files)


def test_ensure_directory__creates(tmp_path):
    target = tmp_path / "nested"
    file_operations.ensure_directory(str(target))
    assert target.exists()


def test_move_file__filesystem_without_hard_links_fails_with_actionable_error(tmp_path, monkeypatch):

    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"photograph")

    def no_hard_links(_src, _dest):
        raise OSError(errno.EPERM, "Operation not permitted")

    monkeypatch.setattr(file_operations.os, "link", no_hard_links)
    with pytest.raises(OSError, match="FAT/exFAT") as raised:
        file_operations.move_file(str(src), str(dest))

    assert raised.value.errno == errno.EPERM
    assert src.read_bytes() == b"photograph"
    assert not dest.exists()


def test_move_file__existing_destination_is_kept(tmp_path):
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"new")
    dest.write_bytes(b"old")

    file_operations.move_file(str(src), str(dest))

    assert dest.read_bytes() == b"old"
    assert src.read_bytes() == b"new"
