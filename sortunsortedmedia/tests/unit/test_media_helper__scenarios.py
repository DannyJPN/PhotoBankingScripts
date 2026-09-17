"""
Unit tests for sortunsortedmedialib/media_helper.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from subprocess import CalledProcessError

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

import sortunsortedmedialib.media_helper as media_helper


def test_open_media_file__missing(monkeypatch):
    monkeypatch.setattr(media_helper.os.path, "exists", lambda _p: False)
    assert media_helper.open_media_file("C:/missing.jpg") is False


def test_is_media_file_and_video():
    assert media_helper.is_media_file("file.jpg") is True
    assert media_helper.is_video_file("file.mp4") is True
    assert media_helper.is_jpg_file("file.jpeg") is True


def test_is_edited_file():
    assert media_helper.is_edited_file("IMG_bw.jpg") is True


def test_find_unmatched_media(monkeypatch):
    monkeypatch.setattr(media_helper, "list_files", lambda _p, recursive=True: ["C:/a.jpg", "C:/b.mp4"])
    monkeypatch.setattr(media_helper, "is_media_file", lambda _p: True)
    monkeypatch.setattr(media_helper.os.path, "basename", lambda p: p.split("/")[-1])
    result = media_helper.find_unmatched_media("unsorted", "target")
    assert "jpg_files" in result


def test_open_appropriate_editor__unsupported(monkeypatch):
    monkeypatch.setattr(media_helper.os.path, "exists", lambda _p: False)
    assert media_helper.open_appropriate_editor("C:/file.unknown") is False
