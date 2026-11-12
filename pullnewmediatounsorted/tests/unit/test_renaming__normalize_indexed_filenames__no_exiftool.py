"""
Unit tests for normalize_indexed_filenames when ExifTool is not installed.

Nothing is mocked except the ExifTool lookup, so the tests cover the real path through
``get_best_creation_date`` and fail if EXIF extraction is attempted without a tool.
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


@pytest.fixture
def no_exiftool_anywhere(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every ExifTool lookup fail, in renaming and in the shared EXIF handler."""
    exif_handler = sys.modules[renaming.get_best_creation_date.__module__]
    monkeypatch.setattr(renaming, "ensure_exiftool", _missing_exiftool)
    monkeypatch.setattr(exif_handler, "ensure_exiftool", _missing_exiftool)


def _create_file(folder: Path, name: str, mtime: datetime) -> Path:
    """Create a file with the given modification time.

    :param folder: Folder for the file.
    :param name: File name.
    :param mtime: Modification time to set.
    :return: Path of the created file.
    """
    path = folder / name
    path.write_text(f"content of {name}")
    os.utime(path, (mtime.timestamp(), mtime.timestamp()))
    return path


def test_renaming__normalize_indexed_filenames__no_exiftool_uses_file_mtime(
    tmp_path: Path, no_exiftool_anywhere: None, caplog: pytest.LogCaptureFixture
) -> None:
    """Without ExifTool the run completes and names the file by its modification date."""
    source = tmp_path / "source"
    reference = tmp_path / "reference"
    source.mkdir()
    reference.mkdir()
    _create_file(source, "PICT0007.JPG", datetime(2026, 6, 12, 12, 0))

    with caplog.at_level("WARNING"):
        normalize_indexed_filenames(source_folders=[str(source)], reference_folder=str(reference), prefix="PICT")

    assert os.listdir(source) == ["PICT20260612_0007.JPG"]
    assert "ExifTool not found" in caplog.text


def test_renaming__normalize_indexed_filenames__no_exiftool_skips_exif_extraction(
    tmp_path: Path, no_exiftool_anywhere: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without ExifTool the EXIF date lookup is not called at all."""
    source = tmp_path / "source"
    reference = tmp_path / "reference"
    source.mkdir()
    reference.mkdir()
    _create_file(source, "NIK_0042.JPG", datetime(2026, 6, 12, 12, 0))
    calls: list[str] = []
    monkeypatch.setattr(
        renaming, "get_best_creation_date", lambda path, tool_path=None: calls.append(path)  # type: ignore[func-returns-value]
    )

    normalize_indexed_filenames(source_folders=[str(source)], reference_folder=str(reference), prefix="NIK_")

    assert calls == []
    assert os.listdir(source) == ["NIK_20260612_0042.JPG"]
