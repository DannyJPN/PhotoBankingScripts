"""
Unit tests for fix_dates.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import fix_dates


def test_parse_date__already_formatted():
    assert fix_dates.parse_date("01.01.2024") == "01.01.2024"


def test_parse_date__iso_datetime():
    assert fix_dates.parse_date("2024-01-15 10:11:12") == "15.01.2024"


def test_parse_date__invalid_returns_original():
    assert fix_dates.parse_date("not-a-date") == "not-a-date"


def test_main__missing_file(monkeypatch):
    monkeypatch.setattr(fix_dates.os.path, "exists", lambda _p: False)
    assert fix_dates.main() == 1
