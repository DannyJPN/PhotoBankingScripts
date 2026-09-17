"""
Unit tests for normalize_indexed_filenames in removealreadysortedoutlib/renaming.py.

Covers the dated-filename format (NIK_YYYYMMDD_XXXX): hash-match against a reference
folder, legacy-format migration, idempotency on already-dated files, missing camera
number handling, and the ExifTool-unavailable fallback to filesystem mtime.
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from removealreadysortedoutlib import renaming
from removealreadysortedoutlib.renaming import normalize_indexed_filenames


@pytest.fixture
def test_folders():
    """Create temporary source/reference directories."""
    source_dir = tempfile.mkdtemp(prefix="test_source_")
    reference_dir = tempfile.mkdtemp(prefix="test_reference_")

    yield source_dir, reference_dir

    shutil.rmtree(source_dir, ignore_errors=True)
    shutil.rmtree(reference_dir, ignore_errors=True)


def create_test_file(directory: str, filename: str, content: str, mtime: datetime) -> str:
    """Create a test file with specific content and modification time."""
    filepath = os.path.join(directory, filename)
    with open(filepath, "w") as f:
        f.write(content)
    timestamp = mtime.timestamp()
    os.utime(filepath, (timestamp, timestamp))
    return filepath


@pytest.fixture(autouse=True)
def no_real_exiftool(monkeypatch):
    """
    Force normalize_indexed_filenames to fall back to filesystem mtime instead of
    depending on a real ExifTool installation, so file mtime fully controls the
    derived date in every test below.
    """
    monkeypatch.setattr(renaming, "ensure_exiftool", lambda: None)
    monkeypatch.setattr(renaming, "get_best_creation_date", lambda _path, tool_path=None: None)


def test_normalize__hash_match_uses_reference_canonical_name(test_folders):
    """A file whose content hash matches a reference file is renamed to that canonical name."""
    source_dir, reference_dir = test_folders
    now = datetime.now()

    content = "same content"
    create_test_file(reference_dir, "PICT20260101_0001.JPG", content, now - timedelta(days=10))
    create_test_file(source_dir, "PICT9999.JPG", content, now - timedelta(days=1))

    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    files = os.listdir(source_dir)
    assert files == ["PICT20260101_0001.JPG"]


def test_normalize__legacy_format_gets_dated_name_from_own_mtime(test_folders):
    """A legacy PICTxxxx file with no reference hash match is renamed using its own mtime and camera number."""
    source_dir, reference_dir = test_folders
    file_date = datetime(2026, 6, 12)

    create_test_file(source_dir, "PICT0042.JPG", "legacy content", file_date)

    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    files = os.listdir(source_dir)
    assert files == ["PICT20260612_0042.JPG"]


def test_normalize__already_dated_file_is_idempotent_across_repeated_runs(test_folders):
    """
    A file already in dated format with no reference hash match must not be renamed,
    even across repeated runs (regression test for the used_names self-collision bug).
    """
    source_dir, reference_dir = test_folders
    file_date = datetime(2026, 6, 12)

    create_test_file(source_dir, "PICT20260612_0042.JPG", "already dated", file_date)

    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")
    assert os.listdir(source_dir) == ["PICT20260612_0042.JPG"]

    # Run again: the file must still be recognized as correctly named, not shifted to _B.
    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")
    assert os.listdir(source_dir) == ["PICT20260612_0042.JPG"]


def test_normalize__missing_camera_number_is_skipped(test_folders):
    """A file matching the prefix but with no parseable camera number is left untouched."""
    source_dir, reference_dir = test_folders

    create_test_file(source_dir, "PICT_not_a_number.JPG", "content", datetime.now())

    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    assert os.listdir(source_dir) == ["PICT_not_a_number.JPG"]


def test_normalize__same_day_camera_number_conflict_gets_suffix(test_folders):
    """Two different-hash files that would generate the same dated name get a _B suffix on the second."""
    source_dir, reference_dir = test_folders
    file_date = datetime(2026, 6, 12)

    # Pre-existing correctly-named file for camera number 0042 on the same day.
    create_test_file(source_dir, "PICT20260612_0042.JPG", "first", file_date)
    # Legacy file that would resolve to the same camera number and date, but different content.
    create_test_file(source_dir, "PICT0042.JPG", "second, different content", file_date)

    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    files = sorted(os.listdir(source_dir))
    assert files == ["PICT20260612_0042.JPG", "PICT20260612_0042_B.JPG"]


def test_normalize__no_matching_files_is_noop(test_folders):
    """An empty (or non-matching) source folder is a no-op and does not raise."""
    source_dir, reference_dir = test_folders

    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    assert os.listdir(source_dir) == []


def test_normalize__exiftool_unavailable_falls_back_to_filesystem_mtime(test_folders, monkeypatch):
    """When ExifTool cannot be located, the function must still complete using mtime."""
    source_dir, reference_dir = test_folders
    file_date = datetime(2026, 6, 12)

    monkeypatch.setattr(renaming, "ensure_exiftool", lambda: (_ for _ in ()).throw(FileNotFoundError("no exiftool")))

    create_test_file(source_dir, "PICT0007.JPG", "content", file_date)

    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    assert os.listdir(source_dir) == ["PICT20260612_0007.JPG"]
