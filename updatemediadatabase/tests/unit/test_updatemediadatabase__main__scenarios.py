"""
Unit tests for updatemediadatabase/updatemediadatabase.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))

import updatemediadatabase as main_module


def test_split_files_by_type():
    result = main_module.split_files_by_type(["a.jpg", "b.mp4", "c.png", "d.txt"])
    assert "a.jpg" in result["jpg"]
    assert "b.mp4" in result["videos"]
    assert "c.png" in result["non_jpg_images"]


def test_get_basename_from_filepath():
    assert main_module.get_basename_from_filepath("C:/path/file.jpg") == "file"


def test_main__exiftool_missing(monkeypatch):
    args = SimpleNamespace(
        media_csv="media.csv",
        limits_csv="limits.csv",
        photo_dir="C:/photos",
        video_dir="C:/videos",
        edit_photo_dir="C:/edit/photos",
        edit_video_dir="C:/edit/videos",
        log_dir="C:/logs",
        debug=False,
        export_report=False,
        report_dir="C:/reports",
        report_format="csv",
    )
    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(main_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(main_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(main_module, "ensure_exiftool", lambda: (_ for _ in ()).throw(RuntimeError("missing")))

    assert main_module.main() is None


def test_parse_arguments__export_report_flags(monkeypatch, tmp_path):
    report_dir = tmp_path / "reports"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "updatemediadatabase.py",
            "--export-report",
            "--report-dir",
            str(report_dir),
            "--report-format",
            "json",
        ],
    )

    args = main_module.parse_arguments()

    assert args.export_report is True
    assert args.report_dir == str(report_dir)
    assert args.report_format == "json"


def test_resolve_report_dir__rejects_empty_value():
    try:
        main_module._resolve_report_dir("   ")
    except ValueError as exc:
        assert "report_dir" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty report_dir")
