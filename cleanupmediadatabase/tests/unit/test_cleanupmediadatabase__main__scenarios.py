"""
Unit tests for cleanupmediadatabase.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "cleanupmediadatabase"
sys.path.insert(0, str(package_root))

import cleanupmediadatabase as main_module


def test_parse_arguments__export_flags(monkeypatch, tmp_path):
    report_dir = tmp_path / "reports"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "cleanupmediadatabase.py",
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


def test_find_missing_records__marks_missing(monkeypatch):
    records = [
        {"Cesta": "C:/exists.jpg", "Soubor": "exists.jpg"},
        {"Cesta": "C:/missing.jpg", "Soubor": "missing.jpg"},
    ]
    monkeypatch.setattr(main_module.os.path, "exists", lambda path: path == "C:/exists.jpg")

    missing = main_module._find_missing_records(records)

    assert len(missing) == 1
    assert missing[0]["Soubor"] == "missing.jpg"
    assert missing[0]["missing"] == "ano"


def test_resolve_report_dir__rejects_empty_value():
    try:
        main_module._resolve_report_dir(" ")
    except ValueError as exc:
        assert "report_dir" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty report_dir")
