"""
Unit tests for _find_files_to_copy.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(createbatch_root))

from createbatchlib.media_preparation import _find_files_to_copy


def test_find_files_to_copy__returns_source_when_supported(tmp_path):
    source = tmp_path / "JPG" / "set" / "image.jpg"
    source.parent.mkdir(parents=True)
    source.write_text("x", encoding="utf-8")

    result = _find_files_to_copy(str(source), include_alternatives=False, supported_formats={".jpg"})

    assert result == [str(source)]


def test_find_files_to_copy__includes_alternatives_when_present(tmp_path):
    source = tmp_path / "JPG" / "set" / "image.jpg"
    alternative = tmp_path / "PNG" / "set" / "image.png"
    source.parent.mkdir(parents=True)
    alternative.parent.mkdir(parents=True)
    source.write_text("x", encoding="utf-8")
    alternative.write_text("y", encoding="utf-8")

    result = _find_files_to_copy(
        str(source),
        include_alternatives=True,
        supported_formats={".jpg", ".png"},
    )

    assert set(result) == {str(source), str(alternative)}


def test_find_files_to_copy__warns_when_format_dir_missing(tmp_path, caplog):
    source = tmp_path / "set" / "image.jpg"
    source.parent.mkdir(parents=True)
    source.write_text("x", encoding="utf-8")

    with caplog.at_level("WARNING"):
        result = _find_files_to_copy(
            str(source),
            include_alternatives=True,
            supported_formats={".jpg", ".png"},
        )

    assert result == [str(source)]
    assert "could not identify format directory" in caplog.text.lower()
