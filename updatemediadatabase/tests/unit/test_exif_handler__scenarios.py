"""
Unit tests for updatemedialdatabaselib/exif_handler.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from subprocess import CalledProcessError

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))

import updatemedialdatabaselib.exif_handler as exif_handler


def test_update_exif_metadata__missing_file(monkeypatch):
    monkeypatch.setattr(exif_handler.os.path, "exists", lambda _p: False)
    assert exif_handler.update_exif_metadata("C:/missing.jpg", {}, "C:/exiftool") is False


def test_update_exif_metadata__missing_tool(monkeypatch):
    def fake_exists(path):
        return path == "C:/file.jpg"

    monkeypatch.setattr(exif_handler.os.path, "exists", fake_exists)
    assert exif_handler.update_exif_metadata("C:/file.jpg", {}, "C:/exiftool") is False


def test_update_exif_metadata__success(monkeypatch):
    monkeypatch.setattr(exif_handler.os.path, "exists", lambda _p: True)

    class DummyResult:
        stdout = "1 image files updated"

    monkeypatch.setattr(exif_handler.subprocess, "run", lambda *_a, **_k: DummyResult())
    assert exif_handler.update_exif_metadata("C:/file.jpg", {"Title": "x"}, "C:/exiftool") is True


def test_update_exif_metadata__subprocess_error(monkeypatch):
    monkeypatch.setattr(exif_handler.os.path, "exists", lambda _p: True)

    def fake_run(*_a, **_k):
        raise CalledProcessError(1, "cmd", stderr="boom")

    monkeypatch.setattr(exif_handler.subprocess, "run", fake_run)
    assert exif_handler.update_exif_metadata("C:/file.jpg", {"Title": "x"}, "C:/exiftool") is False
