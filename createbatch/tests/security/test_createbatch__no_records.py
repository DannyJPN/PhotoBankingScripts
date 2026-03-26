"""
Security-focused tests for createbatch no-records path.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "createbatch"
sys.path.insert(0, str(package_root))

import createbatch


class DummyProcessor:
    def __init__(self, *_a, **_k):
        pass

    def process_records_optimized(self, _records, include_edited=False):
        return {}


def test_main_exits_when_no_records(monkeypatch):
    args = types.SimpleNamespace(
        photo_csv="X:/photo.csv",
        output_folder="X:/out",
        skip_existing=False,
        log_dir="X:/logs",
        debug=False,
        include_edited=False,
        include_alternative_formats=False,
    )

    called = {"prepare": False}

    monkeypatch.setattr(createbatch, "parse_arguments", lambda: args)
    monkeypatch.setattr(createbatch, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(createbatch, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(createbatch, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(createbatch, "ensure_exiftool", lambda: "exiftool")
    monkeypatch.setattr(createbatch, "load_csv", lambda _p: [])
    monkeypatch.setattr(createbatch, "RecordProcessor", DummyProcessor)
    monkeypatch.setattr(createbatch, "prepare_media_file", lambda *_a, **_k: called.__setitem__("prepare", True))

    createbatch.main()
    assert called["prepare"] is False
