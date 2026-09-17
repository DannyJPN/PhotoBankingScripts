"""
Unit tests for givephotobankreadymediafileslib/media_processor.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import media_processor


def test_find_unprocessed_records__filters_and_sorts(monkeypatch):
    monkeypatch.setattr(media_processor.os.path, "exists", lambda _p: True)

    def fake_media_type(path):
        return "video" if path.endswith(".mp4") else "image"

    monkeypatch.setattr(media_processor, "get_media_type", fake_media_type)

    records = [
        {"Originál": "ano", "Soubor": "b.jpg", "Cesta": "C:/b.jpg", "Datum vytvoření": "02.01.2020",
         "Test status": media_processor.STATUS_UNPROCESSED},
        {"Originál": "ano", "Soubor": "a.mp4", "Cesta": "C:/a.mp4", "Datum vytvoření": "01.01.2020",
         "Test status": media_processor.STATUS_UNPROCESSED},
        {"Originál": "ne", "Soubor": "skip.jpg", "Cesta": "C:/skip.jpg", "Datum vytvoření": "01.01.2020",
         "Test status": media_processor.STATUS_UNPROCESSED},
    ]

    result = media_processor.find_unprocessed_records(records)
    assert [r["Soubor"] for r in result] == ["b.jpg", "a.mp4"]


def test_find_unprocessed_records__missing_path_skips(monkeypatch):
    monkeypatch.setattr(media_processor.os.path, "exists", lambda _p: False)

    records = [
        {"Originál": "ano", "Soubor": "a.jpg", "Cesta": "C:/a.jpg", "Test status": media_processor.STATUS_UNPROCESSED}
    ]

    assert media_processor.find_unprocessed_records(records) == []


def test_find_unprocessed_records__invalid_date_falls_back(monkeypatch):
    monkeypatch.setattr(media_processor.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(media_processor, "get_media_type", lambda _p: "image")

    records = [
        {"Originál": "ano", "Soubor": "b.jpg", "Cesta": "C:/b.jpg", "Datum vytvoření": "not-a-date",
         "Test status": media_processor.STATUS_UNPROCESSED},
        {"Originál": "ano", "Soubor": "a.jpg", "Cesta": "C:/a.jpg", "Datum vytvoření": "",
         "Test status": media_processor.STATUS_UNPROCESSED},
    ]

    result = media_processor.find_unprocessed_records(records)
    assert [r["Soubor"] for r in result] == ["a.jpg", "b.jpg"]
