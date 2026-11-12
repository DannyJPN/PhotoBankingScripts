"""
Unit tests for migrate_to_dated_filenames.migrate when ExifTool is not installed.

Nothing is mocked except the ExifTool lookup, so the tests cover the real path through
``get_best_creation_date`` and fail if EXIF extraction is attempted without a tool.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import migrate_to_dated_filenames as migrate_module

FILE_DATE = datetime(2026, 6, 12, 12, 0)


def _missing_exiftool() -> str:
    """Behave like ensure_exiftool on a machine without ExifTool.

    :raises FileNotFoundError: Always.
    """
    raise FileNotFoundError("ExifTool not found")


@pytest.fixture(autouse=True)
def no_exiftool_anywhere(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every ExifTool lookup fail, in the migration script and in the shared EXIF handler."""
    exif_handler = sys.modules[migrate_module.get_best_creation_date.__module__]
    monkeypatch.setattr(migrate_module, "ensure_exiftool", _missing_exiftool)
    monkeypatch.setattr(exif_handler, "ensure_exiftool", _missing_exiftool)


def _create_file(folder: Path, name: str) -> Path:
    """Create a legacy-named file with FILE_DATE as its modification time.

    :param folder: Folder for the file.
    :param name: File name.
    :return: Path of the created file.
    """
    path = folder / name
    path.write_text(f"content of {name}")
    os.utime(path, (FILE_DATE.timestamp(), FILE_DATE.timestamp()))
    return path


def test_migrate_to_dated_filenames__migrate__no_exiftool_uses_file_mtime(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Without ExifTool the migration completes and names the file by its modification date."""
    _create_file(tmp_path, "NIK_0042.JPG")

    with caplog.at_level("WARNING"):
        migrate_module.migrate(str(tmp_path), dry_run=False)

    assert os.listdir(tmp_path) == ["NIK_20260612_0042.JPG"]
    assert "ExifTool not found" in caplog.text


def test_migrate_to_dated_filenames__migrate__no_exiftool_dry_run_completes(tmp_path: Path) -> None:
    """Without ExifTool the dry run completes and renames nothing."""
    _create_file(tmp_path, "PICT0007.JPG")

    migrate_module.migrate(str(tmp_path), dry_run=True)

    assert os.listdir(tmp_path) == ["PICT0007.JPG"]
