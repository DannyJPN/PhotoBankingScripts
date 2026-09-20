"""
Unit tests for normalize_indexed_filenames in pullnewmediatounsortedlib/renaming.py.

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

from pullnewmediatounsortedlib import renaming
from pullnewmediatounsortedlib.renaming import normalize_indexed_filenames


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


def test_normalize__camera_number_above_9999_is_skipped_and_left_untouched(test_folders, caplog):
    """A legacy name whose number cannot fit into four digits must not be renamed to an unparseable name."""
    source_dir, reference_dir = test_folders

    create_test_file(source_dir, "PICT012345.JPG", "wide number", datetime(2026, 6, 12))

    with caplog.at_level("ERROR"):
        normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    assert os.listdir(source_dir) == ["PICT012345.JPG"]
    assert "does not fit" in caplog.text


def test_normalize__rename_skipped_when_destination_exists_logs_warning(test_folders, caplog):
    """If the canonical name is already taken by another source copy, move_file no-ops; that must be reported."""
    source_dir, reference_dir = test_folders
    now = datetime.now()

    create_test_file(reference_dir, "PICT20260101_0001.JPG", "reference content", now - timedelta(days=10))
    create_test_file(source_dir, "PICT9999.JPG", "reference content", now - timedelta(days=1))
    create_test_file(source_dir, "PICT20260101_0001.JPG", "reference content", datetime(2026, 1, 1))

    with caplog.at_level("WARNING"):
        normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    assert sorted(os.listdir(source_dir)) == ["PICT20260101_0001.JPG", "PICT9999.JPG"]
    assert "Rename skipped, destination already exists" in caplog.text


def test_normalize__identical_duplicates_in_different_subfolders_keep_the_same_name(test_folders):
    """Byte-identical copies in different folders are duplicates, not a name conflict (no _B suffix)."""
    source_dir, reference_dir = test_folders
    file_date = datetime(2026, 6, 12)
    for sub in ("a", "b"):
        os.makedirs(os.path.join(source_dir, sub))
        create_test_file(os.path.join(source_dir, sub), "PICT20260612_0042.JPG", "identical content", file_date)

    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    assert sorted(os.listdir(os.path.join(source_dir, "a"))) == ["PICT20260612_0042.JPG"]
    assert sorted(os.listdir(os.path.join(source_dir, "b"))) == ["PICT20260612_0042.JPG"]


def test_normalize__same_name_different_content_in_different_subfolders_gets_suffix(test_folders):
    """Different files that would share one name keep names unique across the whole tree."""
    source_dir, reference_dir = test_folders
    file_date = datetime(2026, 6, 12)
    for sub, content in (("a", "first"), ("b", "second")):
        os.makedirs(os.path.join(source_dir, sub))
        create_test_file(os.path.join(source_dir, sub), "PICT20260612_0042.JPG", content, file_date)

    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    names = sorted(os.listdir(os.path.join(source_dir, "a")) + os.listdir(os.path.join(source_dir, "b")))
    assert names == ["PICT20260612_0042.JPG", "PICT20260612_0042_B.JPG"]


def test_normalize__suffixed_file_is_recognised_and_stays_stable(test_folders):
    """A file that already carries a conflict suffix must not be skipped, renamed or changed on later runs."""
    source_dir, reference_dir = test_folders
    file_date = datetime(2026, 6, 12)
    create_test_file(source_dir, "PICT20260612_0042.JPG", "first", file_date)
    create_test_file(source_dir, "PICT20260612_0042_B.JPG", "second", file_date)

    for _ in range(2):
        normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")
        assert sorted(os.listdir(source_dir)) == ["PICT20260612_0042.JPG", "PICT20260612_0042_B.JPG"]


def test_normalize__name_conflict_check_is_case_insensitive(test_folders):
    """A legacy file must not take a name that differs from an existing one only by letter case."""
    source_dir, reference_dir = test_folders
    file_date = datetime(2026, 6, 12)
    create_test_file(source_dir, "PICT20260612_0042.jpg", "first", file_date)
    create_test_file(source_dir, "PICT0042.JPG", "second, different content", file_date)

    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    assert sorted(os.listdir(source_dir)) == ["PICT20260612_0042.jpg", "PICT20260612_0042_B.JPG"]


def test_normalize__case_only_difference_is_not_a_rename(test_folders):
    """Names are compared case-insensitively, so a name differing only by case needs no rename."""
    source_dir, reference_dir = test_folders
    create_test_file(source_dir, "pict20260612_0042.JPG", "content", datetime(2026, 6, 12))

    normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    assert os.listdir(source_dir) == ["pict20260612_0042.JPG"]


def test_normalize__identical_legacy_copies_that_both_need_renaming_keep_the_same_dated_name(test_folders, caplog):
    """Two byte-identical legacy files in different folders must both get the base name (no _B, no hash error)."""
    source_dir, reference_dir = test_folders
    file_date = datetime(2026, 6, 12)
    for sub in ("a", "b"):
        os.makedirs(os.path.join(source_dir, sub))
        create_test_file(os.path.join(source_dir, sub), "PICT0042.JPG", "identical content", file_date)

    with caplog.at_level("ERROR"):
        normalize_indexed_filenames(source_folder=source_dir, reference_folder=reference_dir, prefix="PICT")

    assert os.listdir(os.path.join(source_dir, "a")) == ["PICT20260612_0042.JPG"]
    assert os.listdir(os.path.join(source_dir, "b")) == ["PICT20260612_0042.JPG"]
    assert "Cannot hash" not in caplog.text
