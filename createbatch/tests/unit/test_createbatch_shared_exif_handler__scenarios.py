"""
Unit tests for createbatch/shared/exif_handler.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

import shared.exif_handler as exif_handler


def test_update_exif_metadata__uses_tool_path_directory(monkeypatch, tmp_path):
    exe = tmp_path / "exiftool.exe"
    exe.write_text("bin", encoding="utf-8")

    monkeypatch.setattr(exif_handler.os, "name", "nt")
    monkeypatch.setattr(exif_handler.os.path, "isdir", lambda p: True)
    monkeypatch.setattr(exif_handler.os.path, "isfile", lambda p: True)
    monkeypatch.setattr(exif_handler.os, "access", lambda p, mode: True)
    monkeypatch.setattr(exif_handler, "shutil", exif_handler.shutil)

    run_args = {}

    def fake_run(args, capture_output, text, check):
        run_args["args"] = args
        return type("Result", (), {"stdout": "ok"})

    monkeypatch.setattr(exif_handler.subprocess, "run", fake_run)

    exif_handler.update_exif_metadata(
        "C:/media/file.jpg",
        {"title": "t"},
        tool_path=str(tmp_path),
    )

    assert run_args["args"][0].endswith("exiftool.exe")


def test_update_exif_metadata__uses_tool_path_file(monkeypatch):
    monkeypatch.setattr(exif_handler.os.path, "isdir", lambda p: False)
    monkeypatch.setattr(exif_handler.os.path, "isfile", lambda p: True)
    monkeypatch.setattr(exif_handler.os, "access", lambda p, mode: True)
    monkeypatch.setattr(exif_handler.shutil, "which", lambda _n: None)

    run_args = {}

    def fake_run(args, capture_output, text, check):
        run_args["args"] = args
        return type("Result", (), {"stdout": "ok"})

    monkeypatch.setattr(exif_handler.subprocess, "run", fake_run)

    exif_handler.update_exif_metadata("C:/media/file.jpg", {}, tool_path="C:/tools/exiftool.exe")

    assert run_args["args"][0] == "C:/tools/exiftool.exe"


def test_update_exif_metadata__falls_back_to_path(monkeypatch):
    monkeypatch.setattr(exif_handler.os.path, "isdir", lambda p: False)
    monkeypatch.setattr(exif_handler.os.path, "isfile", lambda p: False)
    monkeypatch.setattr(exif_handler.os, "access", lambda p, mode: False)
    monkeypatch.setattr(exif_handler.shutil, "which", lambda _n: "C:/bin/exiftool.exe")

    run_args = {}

    def fake_run(args, capture_output, text, check):
        run_args["args"] = args
        return type("Result", (), {"stdout": "ok"})

    monkeypatch.setattr(exif_handler.subprocess, "run", fake_run)

    exif_handler.update_exif_metadata("C:/media/file.jpg", {}, tool_path=None)

    assert run_args["args"][0] == "C:/bin/exiftool.exe"


def test_update_exif_metadata__raises_when_missing(monkeypatch):
    monkeypatch.setattr(exif_handler.os.path, "isdir", lambda p: False)
    monkeypatch.setattr(exif_handler.os.path, "isfile", lambda p: False)
    monkeypatch.setattr(exif_handler.os, "access", lambda p, mode: False)
    monkeypatch.setattr(exif_handler.shutil, "which", lambda _n: None)

    with pytest.raises(RuntimeError):
        exif_handler.update_exif_metadata("C:/media/file.jpg", {}, tool_path=None)


def test_update_exif_metadata__passes_metadata(monkeypatch):
    monkeypatch.setattr(exif_handler.os.path, "isdir", lambda p: False)
    monkeypatch.setattr(exif_handler.os.path, "isfile", lambda p: True)
    monkeypatch.setattr(exif_handler.os, "access", lambda p, mode: True)

    captured = {}

    def fake_run(args, capture_output, text, check):
        captured["args"] = args
        return type("Result", (), {"stdout": "ok"})

    monkeypatch.setattr(exif_handler.subprocess, "run", fake_run)

    exif_handler.update_exif_metadata(
        "C:/media/file.jpg",
        {
            "title": "Title",
            "description": "Desc",
            "keywords": "a,b",
            "datetimeoriginal": "2020:01:01 00:00:00",
        },
        tool_path="C:/tools/exiftool.exe",
    )

    args_str = " ".join(captured["args"])
    assert "-Title=Title" in args_str
    assert "-Description=Desc" in args_str
    assert "-Keywords=a,b" in args_str
    assert "-DateTimeOriginal=2020:01:01 00:00:00" in args_str


def test_update_exif_metadata__subprocess_error_raised(monkeypatch):
    monkeypatch.setattr(exif_handler.os.path, "isdir", lambda p: False)
    monkeypatch.setattr(exif_handler.os.path, "isfile", lambda p: True)
    monkeypatch.setattr(exif_handler.os, "access", lambda p, mode: True)

    def fake_run(*_args, **_kwargs):
        raise exif_handler.subprocess.CalledProcessError(1, "exiftool", stderr="fail")

    monkeypatch.setattr(exif_handler.subprocess, "run", fake_run)

    with pytest.raises(exif_handler.subprocess.CalledProcessError):
        exif_handler.update_exif_metadata("C:/media/file.jpg", {}, tool_path="C:/tools/exiftool.exe")
