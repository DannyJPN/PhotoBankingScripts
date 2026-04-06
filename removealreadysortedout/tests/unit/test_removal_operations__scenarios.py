"""
Unit tests for removealreadysortedoutlib/removal_operations.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

import removealreadysortedoutlib.removal_operations as ops


def test_get_target_files_map__collects(tmp_path):
    file_a = tmp_path / "a.txt"
    file_a.write_text("x", encoding="utf-8")
    result = ops.get_target_files_map(str(tmp_path))
    assert "a.txt" in result


def test_find_duplicates__matches():
    duplicates = ops.find_duplicates(["/tmp/a.txt"], {"a.txt": ["/target/a.txt"]})
    assert "/tmp/a.txt" in duplicates


def test_should_replace_file__target_zero_size(tmp_path):
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("data", encoding="utf-8")
    target.write_text("", encoding="utf-8")

    assert ops.should_replace_file(str(source), str(target)) is True


def test_remove_desktop_ini__removes(tmp_path):
    desktop_ini = tmp_path / "desktop.ini"
    desktop_ini.write_text("x", encoding="utf-8")

    ops.remove_desktop_ini(str(tmp_path))

    assert not desktop_ini.exists()


def test_build_quarantine_path__adds_suffix_for_existing_name(tmp_path):
    quarantine_dir = tmp_path / "quarantine"
    quarantine_dir.mkdir()
    (quarantine_dir / "image.jpg").write_text("taken", encoding="utf-8")

    result = ops._build_quarantine_path(str(quarantine_dir), str(tmp_path / "image.jpg"))

    assert result.endswith("image_001.jpg")
