"""
Unit tests for sortunsortedmedia.py.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

import sortunsortedmedia as sumedia


def make_args(tmp_path, **overrides):
    defaults = dict(
        unsorted_folder=str(tmp_path / "unsorted"),
        target_folder=str(tmp_path / "target"),
        interval=0,
        max_parallel=1,
        debug=False,
        dry_run=False,
        report_dir=str(tmp_path / "reports"),
        report_format="csv",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_parse_arguments__defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["sortunsortedmedia.py"])
    args = sumedia.parse_arguments()
    assert args.unsorted_folder


def test_main__no_unmatched(monkeypatch, tmp_path):
    args = make_args(tmp_path)
    monkeypatch.setattr(sumedia, "parse_arguments", lambda: args)
    monkeypatch.setattr(sumedia, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(sumedia, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(sumedia, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(sumedia, "find_unmatched_media", lambda *_a, **_k: {
        "jpg_files": [], "other_images": [], "videos": [], "edited_images": [], "edited_videos": []
    })

    assert sumedia.main() is None


def test_main__dry_run_writes_reports_and_skips_processing(monkeypatch, tmp_path):
    args = make_args(tmp_path, dry_run=True)
    categories = {
        "jpg_files": [str(tmp_path / "a.jpg")],
        "other_images": [],
        "videos": [],
        "edited_images": [],
        "edited_videos": [],
    }
    process_calls = []
    report_calls = []

    monkeypatch.setattr(sumedia, "parse_arguments", lambda: args)
    monkeypatch.setattr(sumedia, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(sumedia, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(sumedia, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(sumedia, "find_unmatched_media", lambda *_a, **_k: categories)
    monkeypatch.setattr(sumedia, "process_unmatched_files", lambda *_a, **_k: process_calls.append(True))
    monkeypatch.setattr(
        sumedia,
        "write_reports",
        lambda unmatched_categories, report_dir, report_format: report_calls.append(
            (unmatched_categories, report_dir, report_format)
        ),
    )

    assert sumedia.main() is None
    assert process_calls == []
    assert report_calls == [(categories, args.report_dir, args.report_format)]


def test_resolve_report_dir__rejects_existing_file(tmp_path):
    target = tmp_path / "report.csv"
    target.write_text("content", encoding="utf-8")

    try:
        sumedia.resolve_report_dir(str(target))
    except ValueError as exc:
        assert "existing file" in str(exc)
    else:
        raise AssertionError("Expected ValueError for file path")


def test_write_reports__writes_csv_detail_and_summary(tmp_path):
    report_dir = tmp_path / "reports"

    sumedia.write_reports(
        {
            "jpg_files": [str(tmp_path / "one.jpg")],
            "videos": [str(tmp_path / "clip.mp4")],
        },
        str(report_dir),
        "csv",
    )

    generated = sorted(report_dir.iterdir())
    assert len(generated) == 2
    names = [path.name for path in generated]
    assert any(name.startswith("SortUnsortedMediaDryRun_") for name in names)
    assert any(name.startswith("SortUnsortedMediaSummary_") for name in names)


def test_write_reports__writes_json_detail_and_summary(tmp_path):
    report_dir = tmp_path / "reports"

    sumedia.write_reports(
        {
            "jpg_files": [str(tmp_path / "one.jpg")],
            "videos": [],
        },
        str(report_dir),
        "json",
    )

    generated = sorted(report_dir.iterdir())
    assert len(generated) == 2
    assert all(path.suffix == ".json" for path in generated)
