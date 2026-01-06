"""
Security-focused tests for CSV injection sanitization in save_csv.
"""

import csv
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

from shared.file_operations import save_csv


def test_save_csv_sanitizes_formula_injection(tmp_path):
    records = [{"status_main": "=HYPERLINK(\"http://bad\")"}]
    csv_path = tmp_path / "out.csv"

    save_csv(records, str(csv_path))

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert rows[0]["status_main"].startswith("'=")
