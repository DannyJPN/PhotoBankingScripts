"""
Unit tests for createbatch.py preview flow and argument parsing.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(createbatch_root))

import createbatch as createbatch_module


class DummyProcessor:
    return_map = {}

    def __init__(self, status_keyword, prepared_value):
        self.status_keyword = status_keyword
        self.prepared_value = prepared_value

    def process_records_optimized(self, records, include_edited=False):
        return DummyProcessor.return_map


class DummyProgressTracker:
    last_instance = None

    def __init__(self, banks, records_per_bank):
        self.banks = banks
        self.records_per_bank = records_per_bank
        self.started_banks = []
        self.update_calls = []
        self.finish_bank_calls = 0
        self.finish_all_calls = 0
        DummyProgressTracker.last_instance = self

    def start_bank(self, bank):
        self.started_banks.append(bank)

    def update_progress(self, count):
        self.update_calls.append(count)

    def finish_bank(self):
        self.finish_bank_calls += 1

    def finish_all(self):
        self.finish_all_calls += 1


def make_args(tmp_path, **overrides):
    defaults = dict(
        photo_csv=str(tmp_path / "input.csv"),
        output_folder=str(tmp_path / "out"),
        overwrite=False,
        log_dir=str(tmp_path / "logs"),
        debug=False,
        include_edited=False,
        include_alternative_formats=False,
        preview=False,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_createbatch__parse_arguments__preview_and_overwrite_flags(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["createbatch.py", "--preview", "--overwrite"])
    args = createbatch_module.parse_arguments()

    assert args.preview is True
    assert args.overwrite is True


def test_createbatch__main__preview_skips_prepare_media_file(monkeypatch, tmp_path):
    records = [{"Cesta": "a.jpg"}]
    DummyProcessor.return_map = {"AdobeStock": records}

    monkeypatch.setattr(createbatch_module, "parse_arguments", lambda: make_args(tmp_path, preview=True))
    monkeypatch.setattr(createbatch_module, "ensure_directory", lambda _path: None)
    monkeypatch.setattr(createbatch_module, "get_log_filename", lambda _log_dir: str(tmp_path / "log.txt"))
    monkeypatch.setattr(createbatch_module, "setup_logging", lambda **_kwargs: None)
    monkeypatch.setattr(createbatch_module, "ensure_exiftool", lambda: "exiftool")
    monkeypatch.setattr(createbatch_module, "load_csv", lambda _path: records)
    monkeypatch.setattr(createbatch_module, "RecordProcessor", DummyProcessor)
    monkeypatch.setattr(createbatch_module, "UnifiedProgressTracker", DummyProgressTracker)
    monkeypatch.setattr(createbatch_module, "PHOTOBANK_BATCH_SIZE_LIMITS", {"AdobeStock": 0})

    def should_not_run(*_args, **_kwargs):
        raise AssertionError("prepare_media_file should not run in preview mode")

    monkeypatch.setattr(createbatch_module, "prepare_media_file", should_not_run)

    createbatch_module.main()

    tracker = DummyProgressTracker.last_instance
    assert tracker.started_banks == ["AdobeStock"]
    assert tracker.update_calls == [1]
