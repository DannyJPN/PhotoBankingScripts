"""
Unit tests for updatemedialdatabaselib/media_processor.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))

import updatemedialdatabaselib.media_processor as media_processor


def test_get_bank_status__valid():
    assert media_processor.get_bank_status("Bank", True, {}) == "nezpracov no"


def test_extract_category_from_path():
    category = media_processor.extract_category_from_path("C:/a/b/c/d/file.jpg")
    assert category == "a"


def test_calculate_resolution_mpx():
    assert media_processor.calculate_resolution_mpx(2000, 1000) == "2.0"


def test_determine_media_type():
    assert media_processor.determine_media_type("file.jpg", False) == media_processor.TYPE_PHOTO
    assert media_processor.determine_media_type("file.mp4", True) == media_processor.TYPE_EDITED_VIDEO


def test_is_file_in_database():
    assert media_processor.is_file_in_database("C:/file.jpg", {"file.jpg"}) is True


def test_create_database_record__fields():
    metadata = {"Filename": "file.jpg", "Path": "C:/x/y/z/file.jpg", "Width": 100, "Height": 50}
    record = media_processor.create_database_record(metadata, {"ShutterStock": True})
    assert record[media_processor.COLUMN_FILENAME] == "file.jpg"


def test_process_media_file__skips_existing(monkeypatch):
    result = media_processor.process_media_file(
        "C:/file.jpg",
        database=[],
        limits=[],
        exiftool_path="C:/exiftool",
        existing_filenames={"file.jpg"},
    )
    assert result is None


def test_process_media_file__creates_record(monkeypatch):
    monkeypatch.setattr(media_processor, "extract_metadata", lambda *_a, **_k: {"Filename": "file.jpg", "Path": "C:/file.jpg"})
    monkeypatch.setattr(media_processor, "is_edited_file", lambda _f: False)
    monkeypatch.setattr(media_processor, "validate_against_limits", lambda *_a, **_k: {"ShutterStock": True})
    monkeypatch.setattr(media_processor, "create_database_record", lambda *_a, **_k: {"Soubor": "file.jpg"})

    record = media_processor.process_media_file(
        "C:/file.jpg",
        database=[],
        limits=[],
        exiftool_path="C:/exiftool",
        existing_filenames=set(),
    )
    assert record == {"Soubor": "file.jpg"}
