"""
Unit tests for markmediaaschecked.py.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

import markmediaaschecked as mmc
from markmediaascheckedlib import constants


def make_args(tmp_path, **overrides):
    defaults = dict(
        photo_csv_file=str(tmp_path / "input.csv"),
        overwrite=False,
        debug=False,
        log_dir=str(tmp_path / "logs"),
        include_edited=False,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_parse_arguments__defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["markmediaaschecked.py"])
    args = mmc.parse_arguments()
    assert args.photo_csv_file == constants.DEFAULT_PHOTO_CSV_FILE


def test_main__no_records_returns(monkeypatch, tmp_path):
    args = make_args(tmp_path)
    monkeypatch.setattr(mmc, "parse_arguments", lambda: args)
    monkeypatch.setattr(mmc, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(mmc, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(mmc, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(mmc, "load_csv", lambda _p: [])

    assert mmc.main() is None


def test_main__updates_and_saves(monkeypatch, tmp_path):
    args = make_args(tmp_path)
    monkeypatch.setattr(mmc, "parse_arguments", lambda: args)
    monkeypatch.setattr(mmc, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(mmc, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(mmc, "setup_logging", lambda **_k: None)

    records = [{"Status A": constants.STATUS_READY}]
    monkeypatch.setattr(mmc, "load_csv", lambda _p: records)
    monkeypatch.setattr(mmc, "filter_records_by_edit_type", lambda recs, include_edited=False: recs)
    monkeypatch.setattr(mmc, "extract_status_columns", lambda _recs: ["Status A"])
    monkeypatch.setattr(mmc, "filter_ready_records", lambda recs, cols: recs)
    monkeypatch.setattr(mmc, "update_statuses", lambda recs, cols: 1)
    monkeypatch.setattr(mmc, "move_file", lambda *_a, **_k: None)

    saved = {}
    monkeypatch.setattr(mmc, "save_csv", lambda data, path: saved.update({"data": data, "path": path}))

    mmc.main()

    assert saved["data"] == records
