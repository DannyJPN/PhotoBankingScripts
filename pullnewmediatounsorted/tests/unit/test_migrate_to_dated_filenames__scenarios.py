"""
Unit tests for pullnewmediatounsorted/migrate_to_dated_filenames.py.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import migrate_to_dated_filenames as migrate_module

FILE_DATE = datetime(2026, 6, 12)


@pytest.fixture(autouse=True)
def no_real_exiftool(monkeypatch):
    """Use file mtime as the shoot date so the tests do not depend on an ExifTool installation."""
    monkeypatch.setattr(migrate_module, "ensure_exiftool", lambda: None)
    monkeypatch.setattr(migrate_module, "get_best_creation_date", lambda _path, tool_path=None: None)


def create_file(directory: Path, name: str, content: str = "content", mtime: datetime = FILE_DATE) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(content)
    timestamp = mtime.timestamp()
    os.utime(path, (timestamp, timestamp))
    return path


def names(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.rglob("*") if p.is_file())


def test_parse_arguments__defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["migrate_to_dated_filenames.py"])
    args = migrate_module.parse_arguments()
    assert args.folder == migrate_module.DEFAULT_FINAL_TARGET_FOLDER
    assert args.dry_run is False
    assert args.debug is False


def test_parse_arguments__flags(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["migrate_to_dated_filenames.py", "--folder", "X:/lib", "--dry-run", "--debug"])
    args = migrate_module.parse_arguments()
    assert args.folder == "X:/lib"
    assert args.dry_run is True
    assert args.debug is True


def test_collect_legacy_files__returns_only_legacy_names(tmp_path):
    legacy = create_file(tmp_path, "NIK_0001.JPG")
    legacy_raw = create_file(tmp_path / "sub", "PICT0002.NEF")
    create_file(tmp_path, "NIK_20260612_0003.JPG")
    create_file(tmp_path, "IMG_0004.JPG")

    result = migrate_module.collect_legacy_files(str(tmp_path), ["PICT", "NIK_"])

    assert sorted(result) == sorted([legacy, legacy_raw])


def test_migrate__missing_folder_exits(tmp_path):
    with pytest.raises(SystemExit):
        migrate_module.migrate(str(tmp_path / "does_not_exist"), dry_run=False)


def test_migrate__dry_run_changes_nothing(tmp_path):
    create_file(tmp_path, "NIK_0042.JPG")

    migrate_module.migrate(str(tmp_path), dry_run=True)

    assert names(tmp_path) == ["NIK_0042.JPG"]


def test_migrate__renames_legacy_file_using_mtime_and_camera_number(tmp_path):
    create_file(tmp_path, "NIK_0042.JPG")

    migrate_module.migrate(str(tmp_path), dry_run=False)

    assert names(tmp_path) == ["NIK_20260612_0042.JPG"]


def test_migrate__is_idempotent(tmp_path):
    create_file(tmp_path, "NIK_0042.JPG")

    migrate_module.migrate(str(tmp_path), dry_run=False)
    migrate_module.migrate(str(tmp_path), dry_run=False)

    assert names(tmp_path) == ["NIK_20260612_0042.JPG"]


def test_migrate__camera_number_above_9999_is_skipped(tmp_path, caplog):
    create_file(tmp_path, "NIK_012345.JPG")

    with caplog.at_level("WARNING"):
        migrate_module.migrate(str(tmp_path), dry_run=False)

    assert names(tmp_path) == ["NIK_012345.JPG"]
    assert "does not fit" in caplog.text


def test_migrate__identical_copies_in_different_folders_keep_the_same_name(tmp_path):
    create_file(tmp_path / "a", "NIK_0607.NEF", content="identical")
    create_file(tmp_path / "b", "NIK_0607.NEF", content="identical")

    migrate_module.migrate(str(tmp_path), dry_run=False)

    assert names(tmp_path / "a") == ["NIK_20260612_0607.NEF"]
    assert names(tmp_path / "b") == ["NIK_20260612_0607.NEF"]


def test_migrate__same_name_different_content_gets_suffix(tmp_path):
    create_file(tmp_path / "a", "NIK_0607.NEF", content="first")
    create_file(tmp_path / "b", "NIK_0607.NEF", content="second")

    migrate_module.migrate(str(tmp_path), dry_run=False)

    assert sorted(names(tmp_path / "a") + names(tmp_path / "b")) == [
        "NIK_20260612_0607.NEF",
        "NIK_20260612_0607_B.NEF",
    ]


def test_migrate__name_conflict_check_is_case_insensitive(tmp_path):
    create_file(tmp_path, "NIK_20260612_0042.jpg", content="first")
    create_file(tmp_path, "NIK_0042.JPG", content="second, different content")

    migrate_module.migrate(str(tmp_path), dry_run=False)

    assert names(tmp_path) == ["NIK_20260612_0042.jpg", "NIK_20260612_0042_B.JPG"]


def test_migrate__rename_skipped_by_move_file_is_reported_not_counted(tmp_path, monkeypatch, caplog):
    create_file(tmp_path, "NIK_0042.JPG")
    monkeypatch.setattr(migrate_module, "move_file", lambda *_a, **_k: None)

    with caplog.at_level("INFO"):
        migrate_module.migrate(str(tmp_path), dry_run=False)

    assert names(tmp_path) == ["NIK_0042.JPG"]
    assert "Rename skipped, destination already exists" in caplog.text
    assert "Renamed: 0  Skipped: 1" in caplog.text


def test_main__runs_migrate_with_parsed_arguments(monkeypatch, tmp_path):
    calls = {}
    monkeypatch.setattr(sys, "argv", ["migrate_to_dated_filenames.py", "--folder", str(tmp_path), "--dry-run"])
    monkeypatch.setattr(migrate_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(migrate_module, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(migrate_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(migrate_module, "migrate", lambda folder, dry_run: calls.update(folder=folder, dry_run=dry_run))

    migrate_module.main()

    assert calls == {"folder": str(tmp_path), "dry_run": True}


def test_migrate__failed_rename_does_not_leave_a_stale_claim_on_the_new_name(tmp_path, monkeypatch):
    create_file(tmp_path / "a", "NIK_0607.NEF", content="first")
    create_file(tmp_path / "b", "NIK_0607.NEF", content="second")
    real_move = migrate_module.move_file

    def flaky_move(src, dst, overwrite=False):
        if Path(src).parent.name == "a":
            raise PermissionError("locked")
        return real_move(src, dst, overwrite=overwrite)

    monkeypatch.setattr(migrate_module, "move_file", flaky_move)

    migrate_module.migrate(str(tmp_path), dry_run=False)

    assert names(tmp_path / "a") == ["NIK_0607.NEF"]
    assert names(tmp_path / "b") == ["NIK_20260612_0607.NEF"]


def test_migrate__exhausted_name_variants_skip_the_file(tmp_path, caplog):
    taken = ["NIK_20260612_0042.JPG"] + [f"NIK_20260612_0042_{letter}.JPG" for letter in "BCDEFGHIJKLMNOPQRSTUVWXYZ"]
    for index, name in enumerate(taken):
        create_file(tmp_path, name, content=f"content {index}")
    create_file(tmp_path, "NIK_0042.JPG", content="legacy, different content")

    with caplog.at_level("ERROR"):
        migrate_module.migrate(str(tmp_path), dry_run=False)

    assert names(tmp_path) == sorted(taken + ["NIK_0042.JPG"])
    assert "No name variant available" in caplog.text
