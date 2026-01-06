"""
Unit tests for prepare_media_file.
"""

import logging
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(createbatch_root))

import createbatchlib.media_preparation as media_module
from createbatchlib import constants


@pytest.fixture
def patched_dependencies(monkeypatch):
    ensure_calls = []
    copy_calls = []
    exif_calls = []

    monkeypatch.setattr(media_module, "ensure_directory", lambda path: ensure_calls.append(path))

    def fake_copy(src, dest, overwrite=True):
        copy_calls.append((src, dest, overwrite))

    def fake_update(dest, metadata, exif_tool_path):
        exif_calls.append((dest, metadata, exif_tool_path))

    monkeypatch.setattr(media_module, "copy_file", fake_copy)
    monkeypatch.setattr(media_module, "update_exif_metadata", fake_update)
    monkeypatch.setattr(media_module, "sanitize_field", lambda value: value)

    return ensure_calls, copy_calls, exif_calls


def test_prepare_media_file__missing_source_logs_and_returns_empty(tmp_path, caplog, patched_dependencies):
    record = {"Cesta": str(tmp_path / "missing.jpg"), "Shutterstock Status": constants.PREPARED_STATUS_VALUE}

    with caplog.at_level(logging.WARNING):
        result = media_module.prepare_media_file(
            record,
            output_folder=str(tmp_path / "out"),
            exif_tool_path="exiftool",
        )

    assert result == []
    assert "source file does not exist" in caplog.text.lower()


def test_prepare_media_file__copies_to_expected_folder(tmp_path, patched_dependencies):
    ensure_calls, copy_calls, exif_calls = patched_dependencies
    source = tmp_path / "image_bw.jpg"
    source.write_text("data", encoding="utf-8")

    record = {"Cesta": str(source), "Shutterstock Status": constants.PREPARED_STATUS_VALUE}

    result = media_module.prepare_media_file(
        record,
        output_folder=str(tmp_path / "out"),
        exif_tool_path="exiftool",
        overwrite=False,
        bank="Shutterstock",
        include_alternative_formats=False,
    )

    expected_dir = tmp_path / "out" / "Shutterstock" / "jpg" / "_bw"
    expected_dest = expected_dir / source.name

    assert ensure_calls == [str(expected_dir)]
    assert copy_calls == [(str(source), str(expected_dest), False)]
    assert exif_calls and exif_calls[0][0] == str(expected_dest)
    assert result == [str(expected_dest)]


def test_prepare_media_file__bank_mismatch_skips(tmp_path, patched_dependencies):
    source = tmp_path / "image.jpg"
    source.write_text("data", encoding="utf-8")
    record = {"Cesta": str(source), "Shutterstock Status": constants.PREPARED_STATUS_VALUE}

    result = media_module.prepare_media_file(
        record,
        output_folder=str(tmp_path / "out"),
        exif_tool_path="exiftool",
        bank="Adobe Stock",
    )

    assert result == []


def test_prepare_media_file__uses_batch_folder(tmp_path, patched_dependencies):
    ensure_calls, copy_calls, _exif_calls = patched_dependencies
    source = tmp_path / "image.jpg"
    source.write_text("data", encoding="utf-8")
    record = {"Cesta": str(source), "Shutterstock Status": constants.PREPARED_STATUS_VALUE}

    result = media_module.prepare_media_file(
        record,
        output_folder=str(tmp_path / "out"),
        exif_tool_path="exiftool",
        bank="Shutterstock",
        batch_number=2,
    )

    expected_dir = tmp_path / "out" / "Shutterstock" / "batch_002" / "jpg" / "original"
    expected_dest = expected_dir / source.name

    assert ensure_calls == [str(expected_dir)]
    assert copy_calls[0][1] == str(expected_dest)
    assert result == [str(expected_dest)]


def test_prepare_media_file__copy_error_logs_and_continues(tmp_path, patched_dependencies, monkeypatch, caplog):
    source = tmp_path / "image.jpg"
    source.write_text("data", encoding="utf-8")
    record = {"Cesta": str(source), "Shutterstock Status": constants.PREPARED_STATUS_VALUE}

    def fail_copy(_src, _dest, overwrite=True):
        raise OSError("copy failed")

    monkeypatch.setattr(media_module, "copy_file", fail_copy)

    with caplog.at_level(logging.ERROR):
        result = media_module.prepare_media_file(
            record,
            output_folder=str(tmp_path / "out"),
            exif_tool_path="exiftool",
            bank="Shutterstock",
        )

    assert result == []
    assert "failed to copy" in caplog.text.lower()
