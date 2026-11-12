"""
Unit tests for pullnewmediatounsorted.py.
"""

import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "pullnewmediatounsorted"
sys.path.insert(0, str(package_root))

import pullnewmediatounsorted as pnu
from pullnewmediatounsortedlib import constants
from shared import exif_downloader


def _missing_exiftool() -> str:
    """Behave like ensure_exiftool on a machine without ExifTool.

    :raises FileNotFoundError: Always.
    """
    raise FileNotFoundError("ExifTool not found")


@pytest.fixture(autouse=True)
def exiftool_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the start-up ExifTool check pass without a real installation."""
    monkeypatch.setattr(pnu, "ensure_exiftool", lambda: "exiftool")
    monkeypatch.setattr(exif_downloader, "ensure_exiftool", lambda: "exiftool")


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
        return []

    def fake_flatten(*_a, **_k):
        called["flatten"] += 1

    monkeypatch.setattr(pnu, "copy_folder", fake_copy)
    monkeypatch.setattr(pnu, "flatten_folder", fake_flatten)

    pnu.main()

    assert called["copy"] > 0
    assert called["flatten"] == 2


def test_main__conflicts_finish_other_files_but_fail_the_run(monkeypatch, tmp_path, caplog):
    """Copy and flatten everything else, then fail and name every file that was not copied."""
    args = make_args(tmp_path)
    monkeypatch.setattr(pnu, "parse_arguments", lambda: args)
    monkeypatch.setattr(pnu, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(pnu, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(pnu, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(pnu, "unify_duplicate_files", lambda *_a, **_k: None)
    monkeypatch.setattr(pnu, "replace_in_filenames", lambda *_a, **_k: None)
    monkeypatch.setattr(pnu, "normalize_indexed_filenames", lambda *_a, **_k: None)
    copied = []
    flattened = []
    skipped = str(tmp_path / "raid" / "DSC_0001.jpg")

    def conflict(source, destination, **_kwargs):
        copied.append((source, destination))
        return [skipped] if (source, destination) == (args.raid_drive, args.target) else []

    monkeypatch.setattr(pnu, "copy_folder", conflict)
    monkeypatch.setattr(pnu, "flatten_folder", flattened.append)
    with caplog.at_level("INFO"), pytest.raises(FileExistsError, match="Sync incomplete: 1 files"):
        pnu.main()

    assert len(copied) == 16
    assert (args.screens_dropbox, args.target_screen) in copied
    assert flattened == [args.target, args.target_screen]
    assert skipped in caplog.text
    assert "Sync process completed successfully" not in caplog.text


def test_main__missing_exiftool_stops_before_any_file_operation(monkeypatch, tmp_path):
    """Without ExifTool the run fails at start-up, before duplicates are removed or files renamed."""
    args = make_args(tmp_path)
    touched = []
    monkeypatch.setattr(pnu, "parse_arguments", lambda: args)
    monkeypatch.setattr(pnu, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(pnu, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(pnu, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(pnu, "ensure_exiftool", _missing_exiftool)
    for step in ("unify_duplicate_files", "replace_in_filenames", "normalize_indexed_filenames", "copy_folder"):
        monkeypatch.setattr(pnu, step, lambda *_a, _step=step, **_k: touched.append(_step))
    monkeypatch.setattr(pnu, "flatten_folder", lambda *_a, **_k: touched.append("flatten_folder"))

    with pytest.raises(FileNotFoundError, match="ExifTool not found"):
        pnu.main()

    assert touched == []


def test_main__script_exits_with_error_without_exiftool(monkeypatch, tmp_path):
    """Running the script without ExifTool ends with exit code 1 and leaves every file in place."""
    folders = {name: tmp_path / name for name in ("raid", "target", "target_screen", "final", "logs", "empty")}
    for folder in folders.values():
        folder.mkdir()
    (folders["raid"] / "photo_NIK0001.jpg").write_bytes(b"new photo")
    (folders["raid"] / "copy_of_photo.jpg").write_bytes(b"new photo")
    argv = ["pullnewmediatounsorted.py"]
    for option, name in (
        ("--raid_drive", "raid"),
        ("--target", "target"),
        ("--target_screen", "target_screen"),
        ("--final_target", "final"),
        ("--log_dir", "logs"),
        ("--dropbox", "empty"),
        ("--gdrive", "empty"),
        ("--onedrive_auto", "empty"),
        ("--onedrive_manual", "empty"),
        ("--snapbridge", "empty"),
        ("--screens_onedrive", "empty"),
        ("--screens_dropbox", "empty"),
        ("--account_folder", "empty"),
    ):
        argv += [option, str(folders[name])]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(exif_downloader, "ensure_exiftool", _missing_exiftool)

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(package_root / "pullnewmediatounsorted.py"), run_name="__main__")

    assert exit_info.value.code == 1
    assert sorted(p.name for p in folders["raid"].iterdir()) == ["copy_of_photo.jpg", "photo_NIK0001.jpg"]
    assert list(folders["target"].iterdir()) == []


def test_main__script_exits_with_error_on_conflicts(monkeypatch, tmp_path):
    """Running the script ends with exit code 1 and keeps both files when a name clashes."""
    folders = {name: tmp_path / name for name in ("raid", "target", "target_screen", "final", "logs", "empty")}
    for folder in folders.values():
        folder.mkdir()
    (folders["raid"] / "DSC_0001.jpg").write_bytes(b"new photo")
    (folders["target"] / "DSC_0001.jpg").write_bytes(b"other photo")
    argv = ["pullnewmediatounsorted.py"]
    for option, name in (
        ("--raid_drive", "raid"),
        ("--target", "target"),
        ("--target_screen", "target_screen"),
        ("--final_target", "final"),
        ("--log_dir", "logs"),
        ("--dropbox", "empty"),
        ("--gdrive", "empty"),
        ("--onedrive_auto", "empty"),
        ("--onedrive_manual", "empty"),
        ("--snapbridge", "empty"),
        ("--screens_onedrive", "empty"),
        ("--screens_dropbox", "empty"),
        ("--account_folder", "empty"),
    ):
        argv += [option, str(folders[name])]
    monkeypatch.setattr(sys, "argv", argv)

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(package_root / "pullnewmediatounsorted.py"), run_name="__main__")

    assert exit_info.value.code == 1
    assert (folders["raid"] / "DSC_0001.jpg").read_bytes() == b"new photo"
    assert (folders["target"] / "DSC_0001.jpg").read_bytes() == b"other photo"
