"""
Unit tests for givephotobankreadymediafileslib/mediainfo_loader.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import mediainfo_loader


def test_load_media_records__missing_file(monkeypatch):
    monkeypatch.setattr(mediainfo_loader.os.path, "exists", lambda _p: False)
    assert mediainfo_loader.load_media_records("missing.csv") == []


def test_load_media_records__loads_csv(monkeypatch):
    monkeypatch.setattr(mediainfo_loader.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(mediainfo_loader, "load_csv", lambda _p: [{"Soubor": "a.jpg"}])

    result = mediainfo_loader.load_media_records("media.csv")
    assert result == [{"Soubor": "a.jpg"}]


def test_load_categories__missing_file(monkeypatch):
    monkeypatch.setattr(mediainfo_loader.os.path, "exists", lambda _p: False)
    assert mediainfo_loader.load_categories("cats.csv") == {}


def test_load_categories__empty_records(monkeypatch):
    monkeypatch.setattr(mediainfo_loader.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(mediainfo_loader, "load_csv", lambda _p: [])

    assert mediainfo_loader.load_categories("cats.csv") == {}


def test_load_categories__builds_mapping(monkeypatch):
    records = [
        {"ShutterStock": "Animals", "AdobeStock": "Nature"},
        {"ShutterStock": "People", "AdobeStock": ""},
    ]
    monkeypatch.setattr(mediainfo_loader.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(mediainfo_loader, "load_csv", lambda _p: records)

    categories = mediainfo_loader.load_categories("cats.csv")
    assert categories["ShutterStock"] == ["Animals", "People"]
    assert categories["AdobeStock"] == ["Nature"]
