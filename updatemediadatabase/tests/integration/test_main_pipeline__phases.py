"""
Integration tests for updatemediadatabase main phase flow.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))

import updatemediadatabase
from updatemedialdatabaselib.constants import COLUMN_FILENAME


def test_main_runs_all_phases(monkeypatch):
    args = types.SimpleNamespace(
        media_csv="X:/media.csv",
        limits_csv="X:/limits.csv",
        photo_dir="X:/photos",
        video_dir="X:/videos",
        edit_photo_dir="X:/edit_photos",
        edit_video_dir="X:/edit_videos",
        log_dir="X:/logs",
        debug=False,
    )

    store = {"data": []}

    def fake_load_csv(_path):
        return list(store["data"])

    def fake_save_csv_with_backup(data, _path):
        store["data"] = list(data)

    def fake_list_files(directory, recursive=True):
        if directory.endswith("photos"):
            return ["C:/photos/a.jpg", "C:/photos/b.png"]
        if directory.endswith("videos"):
            return ["C:/videos/c.mp4"]
        return []

    def fake_process_media_file(path, _db, _limits, _exiftool, _existing):
        return {COLUMN_FILENAME: Path(path).name}

    monkeypatch.setattr(updatemediadatabase, "parse_arguments", lambda: args)
    monkeypatch.setattr(updatemediadatabase, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(updatemediadatabase, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(updatemediadatabase, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(updatemediadatabase, "ensure_exiftool", lambda: "exiftool")
    monkeypatch.setattr(updatemediadatabase, "load_csv", fake_load_csv)
    monkeypatch.setattr(updatemediadatabase, "save_csv_with_backup", fake_save_csv_with_backup)
    monkeypatch.setattr(updatemediadatabase, "list_files", fake_list_files)
    monkeypatch.setattr(updatemediadatabase, "process_media_file", fake_process_media_file)
    monkeypatch.setattr(updatemediadatabase.os.path, "exists", lambda _p: True)

    updatemediadatabase.main()

    filenames = {row[COLUMN_FILENAME] for row in store["data"]}
    assert filenames == {"a.jpg", "b.png", "c.mp4"}
