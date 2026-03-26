"""
Unit tests for givephotobankreadymediafileslib/media_helper.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from subprocess import CalledProcessError

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import media_helper


def test_open_media_file__missing_file(monkeypatch):
    monkeypatch.setattr(media_helper.os.path, "exists", lambda _p: False)
    assert media_helper.open_media_file("C:/missing.jpg") is False


def test_open_media_file__windows(monkeypatch):
    monkeypatch.setattr(media_helper.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(media_helper.os, "name", "nt")
    called = []
    monkeypatch.setattr(media_helper.os, "startfile", lambda path: called.append(path))

    assert media_helper.open_media_file("C:/file.jpg") is True
    assert called == ["C:/file.jpg"]


def test_open_media_file__posix(monkeypatch):
    monkeypatch.setattr(media_helper.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(media_helper.os, "name", "posix")
    called = []

    def fake_run(cmd, check):
        called.append((cmd, check))

    monkeypatch.setattr(media_helper.subprocess, "run", fake_run)

    assert media_helper.open_media_file("/tmp/file.jpg") is True
    assert called[0][0] == ["xdg-open", "/tmp/file.jpg"]


def test_media_type_helpers():
    assert media_helper.is_media_file("photo.jpg") is True
    assert media_helper.is_video_file("clip.mp4") is True
    assert media_helper.is_image_file("shot.png") is True
    assert media_helper.is_jpg_file("shot.jpeg") is True
    assert media_helper.get_media_type("clip.mp4") == "video"


def test_get_file_info__missing(monkeypatch):
    monkeypatch.setattr(media_helper.os.path, "exists", lambda _p: False)
    assert media_helper.get_file_info("C:/missing.jpg") == {}


def test_get_file_info__returns_fields(monkeypatch):
    monkeypatch.setattr(media_helper.os.path, "exists", lambda _p: True)

    class DummyStat:
        st_size = 123
        st_mtime = 456

    monkeypatch.setattr(media_helper.os, "stat", lambda _p: DummyStat())

    info = media_helper.get_file_info("C:/file.jpg")
    assert info["size"] == 123
    assert info["media_type"] == "image"


def test_process_single_file__missing_file(monkeypatch):
    monkeypatch.setattr(media_helper.os.path, "exists", lambda _p: False)
    success, _path, error = media_helper.process_single_file("C:/missing.jpg")
    assert success is False
    assert "not found" in error.lower()


def test_process_single_file__missing_script(monkeypatch):
    def fake_exists(path):
        return path.endswith(".jpg")

    monkeypatch.setattr(media_helper.os.path, "exists", fake_exists)
    success, _path, error = media_helper.process_single_file("C:/file.jpg")
    assert success is False
    assert "preparemediafile.py not found" in error


def test_process_single_file__subprocess_error(monkeypatch):
    def fake_exists(_p):
        return True

    monkeypatch.setattr(media_helper.os.path, "exists", fake_exists)

    def fake_run(_cmd, check):
        raise CalledProcessError(2, _cmd)

    monkeypatch.setattr(media_helper.subprocess, "run", fake_run)
    success, _path, error = media_helper.process_single_file("C:/file.jpg", media_csv="C:/media.csv")
    assert success is False
    assert "non-zero exit status" in error


def test_process_unmatched_files__stats(monkeypatch):
    records = [
        {"Cesta": "C:/file.jpg", "Soubor": "file.jpg"},
        {"Cesta": "", "Soubor": "missing.jpg"},
    ]

    monkeypatch.setattr(media_helper, "process_single_file", lambda *_args: (True, "C:/file.jpg", ""))
    monkeypatch.setattr(media_helper.time, "sleep", lambda _s: None)

    stats = media_helper.process_unmatched_files(records, max_count=2, interval=1)
    assert stats["processed"] == 1
    assert stats["skipped"] == 1
