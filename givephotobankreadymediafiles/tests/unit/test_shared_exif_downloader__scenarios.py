"""
Unit tests for givephotobankreadymediafiles/shared/exif_downloader.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

import shared.exif_downloader as exif_downloader


def test_ensure_exiftool__returns_path_when_exists(monkeypatch):
    monkeypatch.setattr(exif_downloader, "EXIFTOOL_PATH", "C:/Tools/exiftool.exe")
    monkeypatch.setattr(exif_downloader.os.path, "exists", lambda _p: True)

    assert exif_downloader.ensure_exiftool() == "C:/Tools/exiftool.exe"


def test_ensure_exiftool__raises_when_missing(monkeypatch):
    monkeypatch.setattr(exif_downloader, "EXIFTOOL_PATH", "C:/Tools/exiftool.exe")
    monkeypatch.setattr(exif_downloader.os.path, "exists", lambda _p: False)

    with pytest.raises(FileNotFoundError):
        exif_downloader.ensure_exiftool()
