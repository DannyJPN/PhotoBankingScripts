"""
Unit tests for normalize_indexed_filenames when ExifTool is not installed.

Dated names are permanent, so nothing may be renamed from file-system dates alone.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pullnewmediatounsortedlib import renaming
from pullnewmediatounsortedlib.renaming import normalize_indexed_filenames


def _missing_exiftool() -> str:
    """Behave like ensure_exiftool on a machine without ExifTool.

    :raises FileNotFoundError: Always.
    """
    raise FileNotFoundError("ExifTool not found")


def _create_file(folder: Path, name: str) -> Path:
    """Create a file dated 2026-06-12.

    :param folder: Folder for the file.
    :param name: File name.
    :return: Path of the created file.
    """
    path = folder / name
    path.write_text(f"content of {name}")
    timestamp = datetime(2026, 6, 12, 12, 0).timestamp()
    os.utime(path, (timestamp, timestamp))
    return path


def test_renaming__normalize_indexed_filenames__no_exiftool_raises_and_renames_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without ExifTool the call fails and every legacy file keeps its name."""
    source = tmp_path / "source"
    reference = tmp_path / "reference"
    source.mkdir()
    reference.mkdir()
    _create_file(source, "PICT0007.JPG")
    _create_file(source, "PICT0008.JPG")
    monkeypatch.setattr(renaming, "ensure_exiftool", _missing_exiftool)

    with pytest.raises(FileNotFoundError, match="ExifTool not found"):
        normalize_indexed_filenames(source_folders=[str(source)], reference_folder=str(reference), prefix="PICT")

    assert sorted(os.listdir(source)) == ["PICT0007.JPG", "PICT0008.JPG"]


def test_renaming__normalize_indexed_filenames__no_exiftool_never_reads_dates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without ExifTool no date is read, neither from EXIF nor from the file system."""
    source = tmp_path / "source"
    reference = tmp_path / "reference"
    source.mkdir()
    reference.mkdir()
    _create_file(source, "NIK_0042.JPG")
    calls: list[str] = []

    def record_call(path: str, tool_path: str | None = None) -> None:
        """Record a date lookup.

        :param path: Inspected file.
        :param tool_path: ExifTool path passed by the caller.
        """
        calls.append(path)

    monkeypatch.setattr(renaming, "ensure_exiftool", _missing_exiftool)
    monkeypatch.setattr(renaming, "get_best_creation_date", record_call)

    with pytest.raises(FileNotFoundError):
        normalize_indexed_filenames(source_folders=[str(source)], reference_folder=str(reference), prefix="NIK_")

    assert calls == []
    assert os.listdir(source) == ["NIK_0042.JPG"]
