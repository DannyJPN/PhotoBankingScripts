"""
Unit tests for copy_file and copy_folder: an existing file is never replaced by different content.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.file_operations import copy_file, copy_folder


def test_copy_file__copies_to_missing_destination(tmp_path):
    src = tmp_path / "src.jpg"
    src.write_bytes(b"photo")
    dest = tmp_path / "out" / "src.jpg"

    copy_file(str(src), str(dest))

    assert dest.read_bytes() == b"photo"


def test_copy_file__identical_destination_is_skipped(tmp_path):
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"photo")
    dest.write_bytes(b"photo")

    copy_file(str(src), str(dest))

    assert dest.read_bytes() == b"photo"


def test_copy_file__different_content_is_never_overwritten(tmp_path, caplog):
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"corrupted copy")
    dest.write_bytes(b"original photo")

    with caplog.at_level("ERROR"), pytest.raises(FileExistsError):
        copy_file(str(src), str(dest))

    assert dest.read_bytes() == b"original photo"
    assert "Content conflict" in caplog.text


def test_copy_file__same_size_different_content_is_detected(tmp_path):
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"AAAA")
    dest.write_bytes(b"BBBB")

    with pytest.raises(FileExistsError):
        copy_file(str(src), str(dest))

    assert dest.read_bytes() == b"BBBB"


def test_copy_file__overwrite_disabled_skips_existing_without_check(tmp_path):
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"new")
    dest.write_bytes(b"old")

    copy_file(str(src), str(dest), overwrite=False)

    assert dest.read_bytes() == b"old"


def test_copy_folder__conflict_is_reported_and_other_files_are_still_copied(tmp_path, caplog):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    dest.mkdir()
    (src / "a.jpg").write_bytes(b"different")
    (src / "b.jpg").write_bytes(b"fresh")
    (dest / "a.jpg").write_bytes(b"original")

    with caplog.at_level("ERROR"):
        copy_folder(str(src), str(dest))

    assert (dest / "a.jpg").read_bytes() == b"original"
    assert (dest / "b.jpg").read_bytes() == b"fresh"
    assert "1 files from" in caplog.text