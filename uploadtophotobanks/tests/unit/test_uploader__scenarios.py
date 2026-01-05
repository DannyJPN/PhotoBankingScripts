"""
Unit tests for uploadtophotobanksslib/uploader.py.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

import uploadtophotobanksslib.uploader as uploader


def test_scan_media_folder__filters_extensions(tmp_path, monkeypatch):
    monkeypatch.setattr(uploader, "PHOTOBANK_CONFIGS", {"Bank": {"supported_formats": [".jpg"]}})
    (tmp_path / "a.jpg").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")

    up = uploader.PhotobankUploader(credentials={})
    result = up._scan_media_folder(str(tmp_path))
    assert len(result) == 1
    assert result[0].endswith("a.jpg")


def test_filter_files_for_photobank(monkeypatch):
    monkeypatch.setattr(uploader, "PHOTOBANK_CONFIGS", {"Bank": {"supported_formats": [".jpg"]}})
    up = uploader.PhotobankUploader(credentials={})

    files = ["C:/a.jpg", "C:/b.mp4"]
    result = up._filter_files_for_photobank(files, "Bank")
    assert result == ["C:/a.jpg"]


def test_get_target_directory():
    up = uploader.PhotobankUploader(credentials={})
    uploader.PHOTOBANK_CONFIGS["Alamy"] = {"directories": {"vectors": "/Vectors", "stock": "/Stock"}}
    assert up._get_target_directory("C:/file.eps", "Alamy") == "/Vectors"


def test_get_uploadable_files_count(monkeypatch):
    up = uploader.PhotobankUploader(credentials={})
    monkeypatch.setattr(uploader, "load_csv", lambda _p: [{"File": "x", "Bank status": uploader.VALID_STATUS_FOR_UPLOAD, "Cesta": "C:/file.jpg"}])
    monkeypatch.setattr(uploader, "get_status_column", lambda _p: "Bank status")
    monkeypatch.setattr(uploader.os.path, "exists", lambda _p: True)

    assert up.get_uploadable_files_count("csv.csv", "Bank") == 1


def test_validate_credentials(monkeypatch):
    up = uploader.PhotobankUploader(credentials={"Bank": {"username": "u", "password": "p"}})

    class DummyConnection:
        def is_connected(self):
            return True

    up.connection_manager.get_connection = lambda *_a, **_k: DummyConnection()
    up.connection_manager.disconnect = lambda *_a, **_k: None
    assert up.validate_credentials("Bank") is True
