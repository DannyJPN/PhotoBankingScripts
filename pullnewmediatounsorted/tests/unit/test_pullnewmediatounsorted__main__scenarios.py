"""
Unit tests for pullnewmediatounsorted.py.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "pullnewmediatounsorted"
sys.path.insert(0, str(package_root))

import pullnewmediatounsorted as pnu
from pullnewmediatounsortedlib import constants


def make_args(tmp_path, **overrides):
    defaults = dict(
        raid_drive=str(tmp_path / "raid"),
        dropbox=str(tmp_path / "dropbox"),
        gdrive=str(tmp_path / "gdrive"),
        onedrive_auto=str(tmp_path / "od_auto"),
        onedrive_manual=str(tmp_path / "od_manual"),
        snapbridge=str(tmp_path / "snap"),
        screens_onedrive=str(tmp_path / "screen_od"),
        screens_dropbox=str(tmp_path / "screen_db"),
        account_folder=str(tmp_path / "account"),
        target=str(tmp_path / "target"),
        target_screen=str(tmp_path / "target_screen"),
        final_target=str(tmp_path / "final"),
        log_dir=str(tmp_path / "logs"),
        debug=False,
        index_prefix="PICT",
        index_width=4,
        index_max=10,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_parse_arguments__defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pullnewmediatounsorted.py"])
    args = pnu.parse_arguments()
    assert args.raid_drive == constants.DEFAULT_RAID_DRIVE


def test_main__calls_copy_and_flatten(monkeypatch, tmp_path):
    args = make_args(tmp_path)
    monkeypatch.setattr(pnu, "parse_arguments", lambda: args)
    monkeypatch.setattr(pnu, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(pnu, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(pnu, "setup_logging", lambda **_k: None)

    called = {"copy": 0, "flatten": 0}
    monkeypatch.setattr(pnu, "unify_duplicate_files", lambda *_a, **_k: None)
    monkeypatch.setattr(pnu, "replace_in_filenames", lambda *_a, **_k: None)
    monkeypatch.setattr(pnu, "normalize_indexed_filenames", lambda *_a, **_k: None)

    def fake_copy(*_a, **_k):
        called["copy"] += 1

    def fake_flatten(*_a, **_k):
        called["flatten"] += 1

    monkeypatch.setattr(pnu, "copy_folder", fake_copy)
    monkeypatch.setattr(pnu, "flatten_folder", fake_flatten)

    pnu.main()

    assert called["copy"] > 0
    assert called["flatten"] == 2
