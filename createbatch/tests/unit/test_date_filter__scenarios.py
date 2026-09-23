"""
Unit tests for createbatchlib.date_filter.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(createbatch_root))

from createbatchlib.date_filter import filter_records_by_prepared_date, parse_prepared_date


def test_parse_prepared_date__supports_czech_format():
    parsed = parse_prepared_date("26.03.2026")

    assert parsed is not None
    assert parsed.isoformat() == "2026-03-26"


def test_filter_records_by_prepared_date__keeps_only_in_range():
    records = [
        {"Datum přípravy": "2025-01-01", "Cesta": "old.jpg"},
        {"Datum přípravy": "2025-06-15", "Cesta": "kept.jpg"},
        {"Datum přípravy": "2026-01-01", "Cesta": "new.jpg"},
    ]

    filtered = filter_records_by_prepared_date(
        records,
        "Datum přípravy",
        parse_prepared_date("2025-06-01"),
        parse_prepared_date("2025-12-31"),
    )

    assert filtered == [{"Datum přípravy": "2025-06-15", "Cesta": "kept.jpg"}]
