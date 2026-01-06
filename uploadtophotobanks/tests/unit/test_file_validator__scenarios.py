"""
Unit tests for uploadtophotobanksslib/file_validator.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

import uploadtophotobanksslib.file_validator as file_validator
from uploadtophotobanksslib.file_validator import FileValidator


class DummyImage:
    def __init__(self, mode="RGB", width=100, height=100, fmt="JPEG"):
        self.mode = mode
        self.width = width
        self.height = height
        self.format = fmt

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


def test_validate_file_for_photobank__missing_file(monkeypatch):
    validator = FileValidator()
    monkeypatch.setattr(file_validator.os.path, "exists", lambda _p: False)
    assert validator.validate_file_for_photobank("C:/missing.jpg", "ShutterStock") is False


def test_validate_file_for_photobank__unsupported_photobank(monkeypatch):
    validator = FileValidator()
    monkeypatch.setattr(file_validator.os.path, "exists", lambda _p: True)
    assert validator.validate_file_for_photobank("C:/file.jpg", "Unknown") is False


def test_validate_file_for_photobank__unsupported_extension(monkeypatch):
    validator = FileValidator()
    monkeypatch.setattr(file_validator.os.path, "exists", lambda _p: True)
    assert validator.validate_file_for_photobank("C:/file.txt", "ShutterStock") is False


def test_validate_image__bad_mode(monkeypatch):
    validator = FileValidator()
    monkeypatch.setattr(file_validator.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(file_validator.os.path, "getsize", lambda _p: 10)
    monkeypatch.setattr(file_validator.Image, "open", lambda _p: DummyImage(mode="CMYK"))

    assert validator.validate_file_for_photobank("C:/file.jpg", "ShutterStock") is False


def test_validate_video__size_limit(monkeypatch):
    validator = FileValidator()
    monkeypatch.setattr(file_validator.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(file_validator.os.path, "getsize", lambda _p: 5 * 1024 * 1024 * 1024)
    assert validator.validate_file_for_photobank("C:/file.mp4", "ShutterStock") is False


def test_validate_vector__warns_missing_jpeg(monkeypatch):
    validator = FileValidator()
    monkeypatch.setattr(file_validator.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(file_validator.os.path, "getsize", lambda _p: 10)
    assert validator.validate_file_for_photobank("C:/file.eps", "123RF") is True


def test_clear_cache_and_get_file_info():
    validator = FileValidator()
    validator.image_cache["file"] = {"width": 1}
    assert validator.get_file_info("file") == {"width": 1}
    validator.clear_cache()
    assert validator.get_file_info("file") is None
