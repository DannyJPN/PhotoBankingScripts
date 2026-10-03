"""
Unit tests for removealreadysortedoutlib/renaming.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

from removealreadysortedoutlib.renaming import replace_in_filenames


def test_replace_in_filenames__renames(tmp_path):
    target = tmp_path / "photo_NIK.jpg"
    target.write_text("x", encoding="utf-8")

    replace_in_filenames(str(tmp_path), "_NIK", "NIK_", recursive=False)

    assert not target.exists()
    assert (tmp_path / "photoNIK_.jpg").exists()


def test_replace_in_filenames__removes_source_when_target_name_exists(tmp_path):
    source = tmp_path / "photo_NIK.jpg"
    existing = tmp_path / "photoNIK_.jpg"
    source.write_text("x", encoding="utf-8")
    existing.write_text("x", encoding="utf-8")

    replace_in_filenames(str(tmp_path), "_NIK", "NIK_", recursive=False)

    assert not source.exists()
    assert existing.exists()


def test_replace_in_filenames__no_match_is_noop(tmp_path):
    untouched = tmp_path / "photo.jpg"
    untouched.write_text("x", encoding="utf-8")

    replace_in_filenames(str(tmp_path), "_NIK", "NIK_", recursive=False)

    assert untouched.exists()
