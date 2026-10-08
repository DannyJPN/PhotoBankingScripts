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


def test_handle_duplicate__failed_deletion_is_logged_and_does_not_raise(tmp_path, monkeypatch, caplog):
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("data", encoding="utf-8")
    target.write_text("data", encoding="utf-8")

    def refuse(_path):
        raise PermissionError("denied")

    monkeypatch.setattr(ops, "delete_file", refuse)

    with caplog.at_level("ERROR"):
        ops.handle_duplicate(str(source), [str(target)])

    assert source.exists()
    assert "Failed to remove duplicate" in caplog.text


def test_handle_duplicate__returns_true_when_source_is_deleted(tmp_path):
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("data", encoding="utf-8")
    target.write_text("data", encoding="utf-8")

    assert ops.handle_duplicate(str(source), [str(target)]) is True


def test_handle_duplicate__keeps_source_when_target_changed_after_scan(tmp_path):
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("data", encoding="utf-8")
    target.write_text("replaced since the scan", encoding="utf-8")

    assert ops.handle_duplicate(str(source), [str(target)]) is False
    assert source.exists()


def test_handle_duplicate__keeps_source_when_source_changed_after_scan(tmp_path):
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("edited since the scan", encoding="utf-8")
    target.write_text("data", encoding="utf-8")

    assert ops.handle_duplicate(str(source), [str(target)]) is False
    assert source.exists()


def test_handle_duplicate__uses_a_later_target_that_still_matches(tmp_path):
    source = tmp_path / "source.txt"
    changed = tmp_path / "changed.txt"
    identical = tmp_path / "identical.txt"
    source.write_text("data", encoding="utf-8")
    changed.write_text("other", encoding="utf-8")
    identical.write_text("data", encoding="utf-8")

    assert ops.handle_duplicate(str(source), [str(changed), str(identical)]) is True
    assert not source.exists()


def test_handle_duplicate__keeps_source_when_it_cannot_be_rehashed(tmp_path, monkeypatch, caplog):
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("data", encoding="utf-8")
    target.write_text("data", encoding="utf-8")

    def locked(_path):
        raise PermissionError("locked")

    monkeypatch.setattr(ops, "compute_file_hash", locked)

    with caplog.at_level("ERROR"):
        assert ops.handle_duplicate(str(source), [str(target)]) is False

    assert source.exists()
    assert "Cannot re-hash" in caplog.text


def test_find_duplicates__empty_source_is_never_a_duplicate(tmp_path, caplog):
    empty_source = tmp_path / "empty_source.jpg"
    empty_target = tmp_path / "empty_target.jpg"
    empty_source.write_bytes(b"")
    empty_target.write_bytes(b"")
    target_map = {compute_file_hash(str(empty_target)): [str(empty_target)]}

    with caplog.at_level("WARNING"):
        duplicates = ops.find_duplicates([str(empty_source)], target_map)

    assert duplicates == {}
    assert "1 unsorted files were not checked for duplicates: 1 empty file" in caplog.text


def test_find_duplicates__summary_counts_unreadable_files(tmp_path, caplog):
    missing = tmp_path / "missing.jpg"

    with caplog.at_level("WARNING"):
        duplicates = ops.find_duplicates([str(missing)], {})

    assert duplicates == {}
    assert "1 unreadable" in caplog.text


def test_get_target_hash_map__reuses_given_hashes_without_reading_the_folder(monkeypatch):
    def must_not_hash(*_a, **_k):
        raise AssertionError("target folder hashed again")

    monkeypatch.setattr(ops, "get_hash_map_from_folder", must_not_hash)

    result = ops.get_target_hash_map("X:/target", {"X:/target/a.jpg": "h1", "X:/target/b.jpg": "h1"})

    assert result == {"h1": ["X:/target/a.jpg", "X:/target/b.jpg"]}
