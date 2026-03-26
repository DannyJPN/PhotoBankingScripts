"""
Unit tests for update_exif_data and load_extensions.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

import createbatchlib.update_exif_data as exif_module


class DummyTqdm:
    def __init__(self, total, desc, unit):
        self.total = total
        self.desc = desc
        self.unit = unit

    def update(self, _count):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DummyResult:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.stdout = "ok"
        self.stderr = ""

    def check_returncode(self):
        if self.returncode != 0:
            raise RuntimeError("exiftool failed")


def test_load_extensions__reads_lines(tmp_path):
    file_path = tmp_path / "ext.txt"
    file_path.write_text("jpg\npng\n", encoding="utf-8")

    result = exif_module.load_extensions(str(file_path))

    assert result == ["jpg", "png"]


def test_load_extensions__error_exits(monkeypatch):
    def fail_open(*_args, **_kwargs):
        raise OSError("nope")

    monkeypatch.setattr(exif_module, "open", fail_open)

    with pytest.raises(SystemExit) as excinfo:
        exif_module.load_extensions("missing.txt")

    assert excinfo.value.code == 1


def test_update_exif_data__skips_unsupported(monkeypatch, caplog):
    monkeypatch.setattr(exif_module, "tqdm", DummyTqdm)
    monkeypatch.setattr(exif_module, "load_extensions", lambda _path: ["jpg"])

    run_calls = []

    def fake_run(*_args, **_kwargs):
        run_calls.append(True)
        return DummyResult()

    monkeypatch.setattr(exif_module.subprocess, "run", fake_run)

    items = [{"Cesta": "file.txt"}]

    with caplog.at_level("WARNING"):
        exif_module.update_exif_data(items, "C:/Tools")

    assert "unsupported file type" in caplog.text.lower()
    assert run_calls == []


def test_update_exif_data__runs_exiftool_for_supported(monkeypatch):
    monkeypatch.setattr(exif_module, "tqdm", DummyTqdm)
    monkeypatch.setattr(exif_module, "load_extensions", lambda _path: ["jpg"])

    run_args = {}

    def fake_run(command, capture_output, text):
        run_args["command"] = command
        run_args["capture_output"] = capture_output
        run_args["text"] = text
        return DummyResult()

    monkeypatch.setattr(exif_module.subprocess, "run", fake_run)

    items = [{"Cesta": "photo.jpg", "N zev": "Title", "Kl¡Ÿov  slova": "kw", "Popis": "Desc"}]
    exif_module.update_exif_data(items, "C:/Tools")

    assert "exiftool-12.30" in run_args["command"][0]
    assert "photo.jpg" in run_args["command"]


def test_update_exif_data__run_failure_logged(monkeypatch, caplog):
    monkeypatch.setattr(exif_module, "tqdm", DummyTqdm)
    monkeypatch.setattr(exif_module, "load_extensions", lambda _path: ["jpg"])

    def fake_run(*_args, **_kwargs):
        return DummyResult(returncode=1)

    monkeypatch.setattr(exif_module.subprocess, "run", fake_run)

    items = [{"Cesta": "photo.jpg"}]
    with caplog.at_level("ERROR"):
        exif_module.update_exif_data(items, "C:/Tools")

    assert "error updating exif data for" in caplog.text.lower()
