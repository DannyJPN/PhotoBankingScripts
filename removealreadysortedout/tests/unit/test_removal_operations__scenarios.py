"""
Unit tests for removealreadysortedoutlib/removal_operations.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

import removealreadysortedoutlib.removal_operations as ops
from shared.hash_utils import compute_file_hash


def test_get_target_hash_map__collects(tmp_path):
    file_a = tmp_path / "a.txt"
    file_a.write_text("content", encoding="utf-8")

    result = ops.get_target_hash_map(str(tmp_path))

    h = compute_file_hash(str(file_a))
    assert h in result
    assert str(file_a) in result[h]


def test_find_duplicates__matches_by_content_hash(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("shared content", encoding="utf-8")
    h = compute_file_hash(str(source))

    duplicates = ops.find_duplicates([str(source)], {h: ["/target/a.txt"]})

    assert duplicates == {str(source): ["/target/a.txt"]}


def test_find_duplicates__no_match_when_hash_absent(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("unique content", encoding="utf-8")

    duplicates = ops.find_duplicates([str(source)], {})

    assert duplicates == {}


def test_handle_duplicate__removes_source_when_target_exists(tmp_path):
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("data", encoding="utf-8")
    target.write_text("data", encoding="utf-8")

    ops.handle_duplicate(str(source), [str(target)])

    assert not source.exists()
    assert target.exists()


def test_handle_duplicate__keeps_source_when_no_target_exists(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("data", encoding="utf-8")

    ops.handle_duplicate(str(source), [str(tmp_path / "missing.txt")])

    assert source.exists()


def test_remove_desktop_ini__removes(tmp_path):
    desktop_ini = tmp_path / "desktop.ini"
    desktop_ini.write_text("x", encoding="utf-8")

    ops.remove_desktop_ini(str(tmp_path))

    assert not desktop_ini.exists()
