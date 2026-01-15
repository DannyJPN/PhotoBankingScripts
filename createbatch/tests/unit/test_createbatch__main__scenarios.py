"""
Unit tests for createbatch.py main flow and argument parsing.
"""

import logging
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(createbatch_root))

import createbatch as createbatch_module
from createbatchlib import constants as cb_constants


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


class TruthyEmptyMap:
    def __len__(self):
        return 1

    def keys(self):
        return []

    def items(self):
        return []


def make_args(tmp_path, **overrides):
    defaults = dict(
        photo_csv=str(tmp_path / "input.csv"),
        output_folder=str(tmp_path / "out"),
        overwrite=False,
        log_dir=str(tmp_path / "logs"),
        debug=False,
        include_edited=False,
        include_alternative_formats=False,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.fixture
def common_patches(monkeypatch, tmp_path):
    monkeypatch.setattr(createbatch_module, "ensure_directory", lambda _path: None)
    monkeypatch.setattr(createbatch_module, "get_log_filename", lambda _log_dir: str(tmp_path / "log.txt"))
    monkeypatch.setattr(createbatch_module, "setup_logging", lambda **_kwargs: None)
    monkeypatch.setattr(createbatch_module, "ensure_exiftool", lambda: "exiftool")
    monkeypatch.setattr(createbatch_module, "RecordProcessor", DummyProcessor)
    monkeypatch.setattr(createbatch_module, "UnifiedProgressTracker", DummyProgressTracker)
    return tmp_path


def test_createbatch__parse_arguments__defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["createbatch.py"])
    args = createbatch_module.parse_arguments()

    assert args.photo_csv == cb_constants.DEFAULT_PHOTO_CSV_FILE
    assert args.output_folder == cb_constants.DEFAULT_PROCESSED_MEDIA_FOLDER
    assert args.log_dir == cb_constants.DEFAULT_LOG_DIR
    assert args.overwrite is False
    assert args.debug is False
    assert args.include_edited is False
    assert args.include_alternative_formats is False


def test_createbatch__parse_arguments__flags(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "createbatch.py",
            "--photo_csv",
            str(tmp_path / "photos.csv"),
            "--output_folder",
            str(tmp_path / "out"),
            "--log_dir",
            str(tmp_path / "logs"),
            "--overwrite",
            "--debug",
            "--include-edited",
            "--include-alternative-formats",
        ],
    )
    args = createbatch_module.parse_arguments()

    assert args.photo_csv.endswith("photos.csv")
    assert args.output_folder.endswith("out")
    assert args.log_dir.endswith("logs")
    assert args.overwrite is True
    assert args.debug is True
    assert args.include_edited is True
    assert args.include_alternative_formats is True


def test_createbatch__main__no_prepared_records_exits(common_patches, monkeypatch, caplog):
    DummyProcessor.return_map = {}
    monkeypatch.setattr(createbatch_module, "parse_arguments", lambda: make_args(common_patches))
    monkeypatch.setattr(createbatch_module, "load_csv", lambda _path: [])

    with caplog.at_level(logging.WARNING):
        createbatch_module.main()

    assert "no prepared media records found" in caplog.text.lower()


def test_createbatch__main__no_banks_exits(common_patches, monkeypatch, caplog):
    DummyProcessor.return_map = TruthyEmptyMap()
    monkeypatch.setattr(createbatch_module, "parse_arguments", lambda: make_args(common_patches))
    monkeypatch.setattr(createbatch_module, "load_csv", lambda _path: [])

    with caplog.at_level(logging.WARNING):
        createbatch_module.main()

    assert "no banks found in prepared records" in caplog.text.lower()


def test_createbatch__main__batch_limit_uses_split(common_patches, monkeypatch):
    records = [{"Cesta": "a.jpg"}, {"Cesta": "b.jpg"}]
    DummyProcessor.return_map = {"GettyImages": records}

    def split_batches(input_records, limit):
        assert input_records == records
        assert limit == 1
        return [[records[0]], [records[1]]]

    monkeypatch.setattr(createbatch_module, "parse_arguments", lambda: make_args(common_patches))
    monkeypatch.setattr(createbatch_module, "load_csv", lambda _path: records)
    monkeypatch.setattr(createbatch_module, "split_into_batches", split_batches)
    monkeypatch.setattr(
        createbatch_module,
        "prepare_media_file",
        lambda rec, *_args, **_kwargs: [rec["Cesta"]],
    )
    monkeypatch.setattr(createbatch_module, "PHOTOBANK_BATCH_SIZE_LIMITS", {"GettyImages": 1})

    createbatch_module.main()

    tracker = DummyProgressTracker.last_instance
    assert tracker.started_banks == ["GettyImages"]
    assert tracker.update_calls == [1, 1]
    assert tracker.finish_all_calls == 1


def test_createbatch__main__no_batch_limit_single_batch(common_patches, monkeypatch):
    records = [{"Cesta": "a.jpg"}]
    DummyProcessor.return_map = {"AdobeStock": records}

    def split_should_not_run(*_args, **_kwargs):
        raise AssertionError("split_into_batches should not be called")

    monkeypatch.setattr(createbatch_module, "parse_arguments", lambda: make_args(common_patches))
    monkeypatch.setattr(createbatch_module, "load_csv", lambda _path: records)
    monkeypatch.setattr(createbatch_module, "split_into_batches", split_should_not_run)
    monkeypatch.setattr(
        createbatch_module,
        "prepare_media_file",
        lambda rec, *_args, **_kwargs: [rec["Cesta"]],
    )
    monkeypatch.setattr(createbatch_module, "PHOTOBANK_BATCH_SIZE_LIMITS", {"AdobeStock": 0})

    createbatch_module.main()

    tracker = DummyProgressTracker.last_instance
    assert tracker.update_calls == [1]


def test_createbatch__main__prepare_media_file_error_updates_progress(common_patches, monkeypatch, caplog):
    records = [{"Cesta": "bad.jpg"}, {"Cesta": "good.jpg"}]
    DummyProcessor.return_map = {"Shutterstock": records}

    def prepare_media_file(rec, *_args, **_kwargs):
        if rec["Cesta"] == "bad.jpg":
            raise RuntimeError("boom")
        return [rec["Cesta"]]

    monkeypatch.setattr(createbatch_module, "parse_arguments", lambda: make_args(common_patches))
    monkeypatch.setattr(createbatch_module, "load_csv", lambda _path: records)
    monkeypatch.setattr(createbatch_module, "split_into_batches", lambda recs, _limit: [recs])
    monkeypatch.setattr(createbatch_module, "prepare_media_file", prepare_media_file)
    monkeypatch.setattr(createbatch_module, "PHOTOBANK_BATCH_SIZE_LIMITS", {"Shutterstock": 1})

    with caplog.at_level(logging.ERROR):
        createbatch_module.main()

    tracker = DummyProgressTracker.last_instance
    assert tracker.update_calls == [0, 1]
    assert "error preparing file" in caplog.text.lower()


def test_createbatch__main__zero_total_does_not_crash(common_patches, monkeypatch):
    DummyProcessor.return_map = {"Alamy": []}
    monkeypatch.setattr(createbatch_module, "parse_arguments", lambda: make_args(common_patches))
    monkeypatch.setattr(createbatch_module, "load_csv", lambda _path: [])
    monkeypatch.setattr(createbatch_module, "prepare_media_file", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(createbatch_module, "PHOTOBANK_BATCH_SIZE_LIMITS", {"Alamy": 0})

    createbatch_module.main()
