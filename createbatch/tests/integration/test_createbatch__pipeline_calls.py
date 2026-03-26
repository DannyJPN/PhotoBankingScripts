"""
Integration tests for createbatch main pipeline.
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
        return {"ShutterStock": [{"Cesta": "a.jpg"}, {"Cesta": "b.jpg"}]}


class DummyProgress:
    def __init__(self, _banks, _records_per_bank):
        pass

    def start_bank(self, _bank):
        pass

    def update_progress(self, _count):
        pass

    def finish_bank(self):
        pass

    def finish_all(self):
        pass


def test_main_processes_records(monkeypatch):
    args = types.SimpleNamespace(
        photo_csv="X:/photo.csv",
        output_folder="X:/out",
        skip_existing=False,
        log_dir="X:/logs",
        debug=False,
        include_edited=False,
        include_alternative_formats=False,
    )

    called = {"prepare": 0}

    monkeypatch.setattr(createbatch, "parse_arguments", lambda: args)
    monkeypatch.setattr(createbatch, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(createbatch, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(createbatch, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(createbatch, "ensure_exiftool", lambda: "exiftool")
    monkeypatch.setattr(createbatch, "load_csv", lambda _p: [{"Cesta": "a.jpg"}])
    monkeypatch.setattr(createbatch, "RecordProcessor", DummyProcessor)
    monkeypatch.setattr(createbatch, "UnifiedProgressTracker", DummyProgress)
    monkeypatch.setattr(createbatch, "split_into_batches", lambda records, _limit: [records])

    def fake_prepare(*_a, **_k):
        called["prepare"] += 1
        return ["out.jpg"]

    monkeypatch.setattr(createbatch, "prepare_media_file", fake_prepare)

    createbatch.main()
    assert called["prepare"] == 2
