"""
Unit tests for sortunsortedmedia/shared/exif_downloader.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

import shared.exif_downloader as exif_downloader


def test_ensure_exiftool__missing(monkeypatch):
    monkeypatch.setattr(exif_downloader.os.path, "exists", lambda _p: False)
    try:
        exif_downloader.ensure_exiftool()
    except FileNotFoundError as exc:
        assert "ExifTool not found" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")


def test_ensure_exiftool__exists(monkeypatch):
    monkeypatch.setattr(exif_downloader.os.path, "exists", lambda _p: True)
    assert exif_downloader.ensure_exiftool() == exif_downloader.EXIFTOOL_PATH
