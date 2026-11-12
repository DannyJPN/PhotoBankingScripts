"""
Unit tests for migrate_to_dated_filenames.migrate when ExifTool is not installed.

Dated names are permanent, so the migration must not start without ExifTool.
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
def no_exiftool(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the ExifTool lookup of the migration script fail."""
    monkeypatch.setattr(migrate_module, "ensure_exiftool", _missing_exiftool)


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


@pytest.mark.parametrize("dry_run", [False, True])
def test_migrate_to_dated_filenames__migrate__no_exiftool_exits_and_renames_nothing(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, dry_run: bool
) -> None:
    """Without ExifTool the migration and its dry run end with exit code 1 and rename nothing."""
    _create_file(tmp_path, "NIK_0042.JPG")

    with caplog.at_level("ERROR"), pytest.raises(SystemExit) as exit_info:
        migrate_module.migrate(str(tmp_path), dry_run=dry_run)

    assert exit_info.value.code == 1
    assert os.listdir(tmp_path) == ["NIK_0042.JPG"]
    assert "ExifTool is required" in caplog.text
