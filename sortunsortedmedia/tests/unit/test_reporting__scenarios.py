"""
Unit tests for sortunsortedmedialib/reporting.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

from sortunsortedmedialib.reporting import (  # noqa: E402
    build_detail_records,
    build_report_filename,
    build_summary_records,
)


def test_build_detail_records__flattens_categories():
    records = build_detail_records(
        {
            "jpg_files": ["C:/one.jpg", "C:/two.jpg"],
            "videos": ["C:/clip.mp4"],
        }
    )

    assert records == [
        {"category": "jpg_files", "file_path": "C:/one.jpg"},
        {"category": "jpg_files", "file_path": "C:/two.jpg"},
        {"category": "videos", "file_path": "C:/clip.mp4"},
    ]


def test_build_summary_records__adds_total():
    records = build_summary_records(
        {
            "jpg_files": ["C:/one.jpg", "C:/two.jpg"],
            "videos": ["C:/clip.mp4"],
        }
    )

    assert records == [
        {"category": "jpg_files", "count": "2"},
        {"category": "videos", "count": "1"},
        {"category": "total", "count": "3"},
    ]


def test_build_report_filename__uses_prefix_and_extension():
    filename = build_report_filename("SortUnsortedMediaDryRun", "csv")

    assert filename.startswith("SortUnsortedMediaDryRun_")
    assert filename.endswith(".csv")
