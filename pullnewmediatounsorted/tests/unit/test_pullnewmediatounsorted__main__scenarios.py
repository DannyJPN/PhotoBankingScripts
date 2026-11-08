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
        report_dir=str(tmp_path / "reports"),
        report_format="csv",
        export_report=False,
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


def test_main__export_report_writes_new_files_report(monkeypatch, tmp_path):
    args = make_args(tmp_path, export_report=True)
    monkeypatch.setattr(pnu, "parse_arguments", lambda: args)
    monkeypatch.setattr(pnu, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(pnu, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(pnu, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(pnu, "unify_duplicate_files", lambda *_a, **_k: None)
    monkeypatch.setattr(pnu, "replace_in_filenames", lambda *_a, **_k: None)
    monkeypatch.setattr(pnu, "normalize_indexed_filenames", lambda *_a, **_k: None)
    monkeypatch.setattr(pnu, "copy_folder", lambda *_a, **_k: None)
    monkeypatch.setattr(pnu, "flatten_folder", lambda *_a, **_k: None)
    monkeypatch.setattr(pnu, "_collect_basename_set", lambda *_a, **_k: set())
    monkeypatch.setattr(
        pnu,
        "_build_new_files_report",
        lambda *_a, **_k: [{"category": "media", "file_path": "C:/file.jpg"}],
    )

    report_calls = []
    monkeypatch.setattr(
        pnu,
        "_write_new_files_report",
        lambda records, report_dir, report_format: report_calls.append((records, report_dir, report_format)),
    )

    pnu.main()

    assert report_calls == [
        ([{"category": "media", "file_path": "C:/file.jpg"}], args.report_dir, args.report_format)
    ]


def test_resolve_report_dir__rejects_existing_file(tmp_path):
    target = tmp_path / "report.csv"
    target.write_text("content", encoding="utf-8")

    try:
        pnu._resolve_report_dir(str(target))
    except ValueError as exc:
        assert "existing file" in str(exc)
    else:
        raise AssertionError("Expected ValueError for file path")


def test_write_new_files_report__writes_csv(tmp_path):
    report_dir = tmp_path / "reports"

    pnu._write_new_files_report(
        [{"category": "media", "file_path": "C:/file.jpg"}],
        str(report_dir),
        "csv",
    )

    generated = list(report_dir.iterdir())
    assert len(generated) == 1
    assert generated[0].name.startswith("PullNewMediaNewFiles_")
    assert generated[0].suffix == ".csv"


def test_build_new_files_report__filters_preexisting_basenames(tmp_path):
    media_target = tmp_path / "target"
    screen_target = tmp_path / "screens"
    media_target.mkdir()
    screen_target.mkdir()

    media_old = media_target / "old.jpg"
    media_new = media_target / "new.jpg"
    screen_new = screen_target / "Screen_1.png"
    media_old.write_text("old", encoding="utf-8")
    media_new.write_text("new", encoding="utf-8")
    screen_new.write_text("screen", encoding="utf-8")

    records = pnu._build_new_files_report(
        {"old.jpg"},
        set(),
        str(media_target),
        str(screen_target),
    )

    assert records == [
        {"category": "media", "file_path": str(media_new)},
        {"category": "screenshots", "file_path": str(screen_new)},
    ]
