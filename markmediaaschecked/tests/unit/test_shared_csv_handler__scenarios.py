"""
Unit tests for markmediaaschecked/shared/csv_handler.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

import shared.csv_handler as csv_handler


def test_load_csv__success(monkeypatch):
    monkeypatch.setattr(csv_handler, "detect_encoding", lambda _p: "utf-8")

    class DummyDf:
        def to_dict(self, orient="records"):
            return [{"a": 1}]

    monkeypatch.setattr(csv_handler.pd, "read_csv", lambda *_a, **_k: DummyDf())

    data, encoding = csv_handler.load_csv("file.csv")
    assert data == [{"a": 1}]
    assert encoding == "utf-8"


def test_load_csv__failure(monkeypatch):
    monkeypatch.setattr(csv_handler, "detect_encoding", lambda _p: "utf-8")
    monkeypatch.setattr(csv_handler.pd, "read_csv", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")))

    try:
        csv_handler.load_csv("file.csv")
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("Expected SystemExit")


def test_save_csv__success(monkeypatch, tmp_path):
    file_path = tmp_path / "data.csv"
    file_path.write_text("a,b\n1,2\n", encoding="utf-8")

    called = []
    monkeypatch.setattr(csv_handler.shutil, "copy", lambda *_a, **_k: called.append(True))

    class DummyDf:
        def __init__(self, data):
            self.data = data

        def to_csv(self, *_a, **_k):
            called.append("saved")

    monkeypatch.setattr(csv_handler.pd, "DataFrame", lambda data: DummyDf(data))

    csv_handler.save_csv([{"a": 1}], str(file_path), "utf-8")
    assert "saved" in called


def test_save_csv__failure(monkeypatch, tmp_path):
    file_path = tmp_path / "data.csv"
    file_path.write_text("a,b\n1,2\n", encoding="utf-8")

    monkeypatch.setattr(csv_handler.shutil, "copy", lambda *_a, **_k: None)
    monkeypatch.setattr(csv_handler.pd, "DataFrame", lambda _data: (_ for _ in ()).throw(RuntimeError("boom")))

    try:
        csv_handler.save_csv([{"a": 1}], str(file_path), "utf-8")
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("Expected SystemExit")
