"""
Unit tests: unify_duplicate_files returns the folder's hash map after unification.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

from shared.file_operations import unify_duplicate_files
from shared.hash_utils import compute_file_hash


def test_unify_duplicate_files__returns_paths_after_renaming(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "a.jpg").write_bytes(b"same")
    (sub / "longer_name.jpg").write_bytes(b"same")
    (tmp_path / "unique.jpg").write_bytes(b"unique")

    result = unify_duplicate_files(str(tmp_path))

    same_hash = compute_file_hash(str(tmp_path / "a.jpg"))
    assert result == {
        str(tmp_path / "a.jpg"): same_hash,
        str(sub / "a.jpg"): same_hash,
        str(tmp_path / "unique.jpg"): compute_file_hash(str(tmp_path / "unique.jpg")),
    }


def test_unify_duplicate_files__returns_map_when_nothing_to_unify(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"one")

    result = unify_duplicate_files(str(tmp_path))

    assert result == {str(tmp_path / "a.jpg"): compute_file_hash(str(tmp_path / "a.jpg"))}


def test_unify_duplicate_files__returns_empty_map_for_empty_folder(tmp_path):
    assert unify_duplicate_files(str(tmp_path)) == {}
