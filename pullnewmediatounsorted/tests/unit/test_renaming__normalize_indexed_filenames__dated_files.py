"""
Unit tests: already-dated files never enter the normalize_indexed_filenames rename path.
"""

import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pullnewmediatounsortedlib import renaming
from pullnewmediatounsortedlib.renaming import normalize_indexed_filenames


@pytest.fixture
def test_folders():
    source_dir = tempfile.mkdtemp(prefix="test_source_")
    reference_dir = tempfile.mkdtemp(prefix="test_reference_")

    yield source_dir, reference_dir

    shutil.rmtree(source_dir, ignore_errors=True)
    shutil.rmtree(reference_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def no_real_exiftool(monkeypatch):
    monkeypatch.setattr(renaming, "ensure_exiftool", lambda: (_ for _ in ()).throw(FileNotFoundError("no exiftool")))


def create_file(directory: str, filename: str, content: str, mtime: datetime) -> str:
    filepath = os.path.join(directory, filename)
    with open(filepath, "w") as f:
        f.write(content)
    timestamp = mtime.timestamp()
    os.utime(filepath, (timestamp, timestamp))
    return filepath


def test_normalize__dated_file_is_not_renamed_when_mtime_changes(test_folders):
    source_dir, reference_dir = test_folders
    create_file(source_dir, "NIK_20260101_0001.MP4", "video", datetime(2026, 1, 1))

    normalize_indexed_filenames(source_folders=[source_dir], reference_folder=reference_dir, prefix="NIK_")
    create_file(source_dir, "NIK_20260101_0001.MP4", "video", datetime(2026, 5, 5))
    normalize_indexed_filenames(source_folders=[source_dir], reference_folder=reference_dir, prefix="NIK_")

    assert os.listdir(source_dir) == ["NIK_20260101_0001.MP4"]


def test_normalize__dated_file_still_blocks_legacy_name_collision(test_folders):
    source_dir, reference_dir = test_folders
    create_file(source_dir, "NIK_20260612_0042.JPG", "dated, first", datetime(2026, 6, 12))
    create_file(source_dir, "NIK_0042.JPG", "legacy, different content", datetime(2026, 6, 12))

    normalize_indexed_filenames(source_folders=[source_dir], reference_folder=reference_dir, prefix="NIK_")

    assert sorted(os.listdir(source_dir)) == ["NIK_20260612_0042.JPG", "NIK_20260612_0042_B.JPG"]


def test_normalize__prefix_match_is_anchored(test_folders):
    source_dir, reference_dir = test_folders
    create_file(source_dir, "XNIK_0042.JPG", "content", datetime(2026, 6, 12))

    normalize_indexed_filenames(source_folders=[source_dir], reference_folder=reference_dir, prefix="NIK_")

    assert os.listdir(source_dir) == ["XNIK_0042.JPG"]


def test_normalize__different_files_in_two_source_folders_never_share_a_name(test_folders, tmp_path):
    source_dir, reference_dir = test_folders
    other_source = str(tmp_path / "other_source")
    os.makedirs(other_source)
    create_file(source_dir, "NIK_0042.JPG", "from card A", datetime(2026, 6, 12))
    create_file(other_source, "NIK_0042.JPG", "from card B, different", datetime(2026, 6, 12))

    normalize_indexed_filenames(
        source_folders=[source_dir, other_source], reference_folder=reference_dir, prefix="NIK_"
    )

    assert sorted(os.listdir(source_dir) + os.listdir(other_source)) == [
        "NIK_20260612_0042.JPG",
        "NIK_20260612_0042_B.JPG",
    ]


def test_normalize__identical_files_in_two_source_folders_get_the_same_name(test_folders, tmp_path):
    source_dir, reference_dir = test_folders
    other_source = str(tmp_path / "other_source")
    os.makedirs(other_source)
    create_file(source_dir, "NIK_0042.JPG", "same shot", datetime(2026, 6, 12))
    create_file(other_source, "NIK_0042.JPG", "same shot", datetime(2026, 6, 12))

    normalize_indexed_filenames(
        source_folders=[source_dir, other_source], reference_folder=reference_dir, prefix="NIK_"
    )

    assert os.listdir(source_dir) == ["NIK_20260612_0042.JPG"]
    assert os.listdir(other_source) == ["NIK_20260612_0042.JPG"]


def test_normalize__lowercase_legacy_prefix_is_normalized(test_folders):
    source_dir, reference_dir = test_folders
    create_file(source_dir, "nik_0042.JPG", "content", datetime(2026, 6, 12))

    normalize_indexed_filenames(source_folders=[source_dir], reference_folder=reference_dir, prefix="NIK_")

    assert os.listdir(source_dir) == ["NIK_20260612_0042.JPG"]


def test_normalize__lowercase_dated_file_still_blocks_legacy_name_collision(test_folders):
    source_dir, reference_dir = test_folders
    create_file(source_dir, "nik_20260612_0042.JPG", "dated, first", datetime(2026, 6, 12))
    create_file(source_dir, "NIK_0042.JPG", "legacy, different content", datetime(2026, 6, 12))

    normalize_indexed_filenames(source_folders=[source_dir], reference_folder=reference_dir, prefix="NIK_")

    assert sorted(os.listdir(source_dir)) == ["NIK_20260612_0042_B.JPG", "nik_20260612_0042.JPG"]


def test_normalize__failed_rename_of_non_owner_does_not_take_over_the_name(test_folders, tmp_path, monkeypatch):
    source_dir, reference_dir = test_folders
    other_source = str(tmp_path / "other_source")
    os.makedirs(other_source)
    failing = create_file(source_dir, "NIK_0042.JPG", "card A", datetime(2026, 6, 12))
    owner = create_file(other_source, "NIK_0042.JPG", "card B", datetime(2026, 6, 13))

    real_move = renaming.move_file

    def move_failing_once(src, dst, overwrite=False):
        if src == failing:
            raise OSError("locked")
        real_move(src, dst, overwrite=overwrite)

    seen: list[dict[str, str]] = []
    real_resolve = renaming.resolve_name_conflict

    def spy_resolve(base_name, used_names, same_content=None):
        seen.append(dict(used_names))
        return real_resolve(base_name, used_names, same_content=same_content)

    monkeypatch.setattr(renaming, "move_file", move_failing_once)
    monkeypatch.setattr(renaming, "resolve_name_conflict", spy_resolve)

    normalize_indexed_filenames(
        source_folders=[source_dir, other_source], reference_folder=reference_dir, prefix="NIK_"
    )

    legacy_key = renaming.name_key("NIK_0042.JPG")
    assert seen[1].get(legacy_key) != failing
    assert os.listdir(other_source) == ["NIK_20260613_0042.JPG"]
    assert os.path.exists(failing) and not os.path.exists(owner)


def test_normalize__skipped_files_are_summarised(test_folders, monkeypatch, caplog):
    source_dir, reference_dir = test_folders
    create_file(source_dir, "NIK_0042.JPG", "content", datetime(2026, 6, 12))
    create_file(source_dir, "NIK_123456.JPG", "too wide", datetime(2026, 6, 12))

    def refuse(*_a, **_k):
        raise OSError("locked")

    monkeypatch.setattr(renaming, "move_file", refuse)

    with caplog.at_level("WARNING"):
        normalize_indexed_filenames(source_folders=[source_dir], reference_folder=reference_dir, prefix="NIK_")

    assert "2 legacy 'NIK_' files were left unrenamed" in caplog.text
    assert "1 rename failed" in caplog.text
    assert "1 camera number out of range" in caplog.text
