"""
Unit tests for replace_in_filenames.
"""

import sys
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "pullnewmediatounsorted"
sys.path.insert(0, str(package_root))

from pullnewmediatounsortedlib.renaming import replace_in_filenames
from shared import file_operations


def test_replace_in_filenames__renames(tmp_path):
    target = tmp_path / "photo_NIK.jpg"
    target.write_text("x", encoding="utf-8")

    replace_in_filenames(str(tmp_path), "_NIK", "NIK_", recursive=False)

    assert not target.exists()
    assert (tmp_path / "photoNIK_.jpg").exists()


@pytest.mark.parametrize("existing_bytes", [b"source", b"different"])
def test_replace_in_filenames__collision_keeps_both_files(tmp_path, caplog, existing_bytes):
    """A matching name never authorizes deletion, even for identical content."""
    source = tmp_path / "photo_NIK.jpg"
    existing = tmp_path / "photoNIK_.jpg"
    source.write_bytes(b"source")
    existing.write_bytes(existing_bytes)

    with caplog.at_level("WARNING"):
        replace_in_filenames(str(tmp_path), "_NIK", "NIK_", recursive=False)

    assert source.read_bytes() == b"source"
    assert existing.read_bytes() == existing_bytes
    assert "Name collision" in caplog.text


def test_replace_in_filenames__concurrent_collision_keeps_both_files(tmp_path, monkeypatch, caplog):
    """Exercise a destination created after the initial existence checks."""
    source = tmp_path / "photo_NIK.jpg"
    existing = tmp_path / "photoNIK_.jpg"
    source.write_bytes(b"source")
    real_link = file_operations.os.link

    def create_competing_target(src, dest):
        Path(dest).write_bytes(b"concurrent file")
        real_link(src, dest)

    monkeypatch.setattr(file_operations.os, "link", create_competing_target)
    with caplog.at_level("WARNING"):
        replace_in_filenames(str(tmp_path), "_NIK", "NIK_", recursive=False)

    assert source.read_bytes() == b"source"
    assert existing.read_bytes() == b"concurrent file"
    assert "Name collision" in caplog.text
