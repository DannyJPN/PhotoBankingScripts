"""
Unit tests for removealreadysortedout/shared/exif_handler.py.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

import shared.exif_handler as exif_handler


def test_extract_exif_dates__no_data(monkeypatch):
    monkeypatch.setattr(exif_handler, "ensure_exiftool", lambda *_a, **_k: "tool")
    monkeypatch.setattr(exif_handler.subprocess, "run", lambda *_a, **_k: type("R", (), {"stdout": "[]"})())
    assert exif_handler.extract_exif_dates("C:/file.jpg") == []


def test_extract_exif_dates__returns_dates(monkeypatch):
    monkeypatch.setattr(exif_handler, "ensure_exiftool", lambda *_a, **_k: "tool")
    payload = '[{"CreateDate": "2024:01:02 10:11:12"}]'
    monkeypatch.setattr(exif_handler.subprocess, "run", lambda *_a, **_k: type("R", (), {"stdout": payload})())
    dates = exif_handler.extract_exif_dates("C:/file.jpg")
    assert isinstance(dates[0], datetime)


def test_update_exif_metadata__raises(monkeypatch):
    monkeypatch.setattr(exif_handler, "ensure_exiftool", lambda *_a, **_k: "tool")
    monkeypatch.setattr(exif_handler.subprocess, "run", lambda *_a, **_k: (_ for _ in ()).throw(CalledProcessError(1, "cmd")))
    try:
        exif_handler.update_exif_metadata("C:/file.jpg", {"Title": "x"})
    except CalledProcessError:
        assert True
    else:
        raise AssertionError("Expected CalledProcessError")


def test_get_best_creation_date__fallback(monkeypatch):
    monkeypatch.setattr(exif_handler, "extract_exif_dates", lambda *_a, **_k: [])
    monkeypatch.setattr(exif_handler.os.path, "getctime", lambda _p: 1)
    monkeypatch.setattr(exif_handler.os.path, "getmtime", lambda _p: 2)
    result = exif_handler.get_best_creation_date("C:/file.jpg")
    assert result is not None
