"""
Unit tests for updatemedialdatabaselib/photo_analyzer.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from subprocess import CalledProcessError

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))

import updatemedialdatabaselib.photo_analyzer as photo_analyzer


def test_extract_metadata__missing_file(monkeypatch):
    monkeypatch.setattr(photo_analyzer.os.path, "exists", lambda _p: False)
    assert photo_analyzer.extract_metadata("C:/missing.jpg", "C:/exiftool") == {}


def test_extract_metadata__missing_tool(monkeypatch):
    def fake_exists(path):
        return path == "C:/file.jpg"

    monkeypatch.setattr(photo_analyzer.os.path, "exists", fake_exists)
    assert photo_analyzer.extract_metadata("C:/file.jpg", "C:/exiftool") == {}


def test_extract_metadata__exiftool_failure(monkeypatch):
    monkeypatch.setattr(photo_analyzer.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(photo_analyzer.os.path, "getsize", lambda _p: 10)
    monkeypatch.setattr(photo_analyzer.os.path, "getmtime", lambda _p: 0)

    def fake_run(*_a, **_k):
        raise CalledProcessError(1, "cmd", stderr="boom")

    monkeypatch.setattr(photo_analyzer.subprocess, "run", fake_run)
    metadata = photo_analyzer.extract_metadata("C:/file.jpg", "C:/exiftool")
    assert metadata["Filename"] == "file.jpg"


def test_extract_metadata__parses_json(monkeypatch):
    monkeypatch.setattr(photo_analyzer.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(photo_analyzer.os.path, "getsize", lambda _p: 10)
    monkeypatch.setattr(photo_analyzer.os.path, "getmtime", lambda _p: 0)

    payload = json.dumps([{"ImageWidth": 100, "ImageHeight": 50, "DateTimeOriginal": "2024:01:02 00:00:00"}])

    class DummyResult:
        stdout = payload

    monkeypatch.setattr(photo_analyzer.subprocess, "run", lambda *_a, **_k: DummyResult())
    metadata = photo_analyzer.extract_metadata("C:/file.jpg", "C:/exiftool")
    assert metadata["Width"] == 100
    assert metadata["Height"] == 50


def test_validate_against_limits__video_uses_typed_limits():
    metadata = {"Type": photo_analyzer.TYPE_VIDEO, "Width": 1920, "Height": 1080}
    limits = [{
        "Banka": "Test",
        "typ": "Video",
        "šířka": "1920",
        "výška": "1080",
        "rozlišení": "2"
    }]
    results = photo_analyzer.validate_against_limits(metadata, limits)
    assert results["Test"] is True


def test_validate_against_limits__vector_ignores_photo_limits():
    metadata = {"Type": photo_analyzer.TYPE_VECTOR, "Width": 100, "Height": 100}
    limits = [{
        "Banka": "Test",
        "šířka": "2000",
        "výška": "2000",
        "rozlišení": "4"
    }]
    results = photo_analyzer.validate_against_limits(metadata, limits)
    assert results["Test"] is True


def test_validate_against_limits__missing_dims():
    metadata = {"Type": photo_analyzer.TYPE_PHOTO}
    limits = [{"Banka": "Test"}]
    results = photo_analyzer.validate_against_limits(metadata, limits)
    assert results["Test"] is True
