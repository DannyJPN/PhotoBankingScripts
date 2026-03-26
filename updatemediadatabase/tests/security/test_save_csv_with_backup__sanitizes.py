"""
Security-focused tests for CSV injection sanitization in save_csv_with_backup.
"""

import csv
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))

from shared.file_operations import save_csv_with_backup


def test_save_csv_with_backup_sanitizes_formula(tmp_path):
    csv_path = tmp_path / "media.csv"
    csv_path.write_text("col\nsafe\n", encoding="utf-8-sig")

    records = [{"col": "=SUM(1,2)"}]
    save_csv_with_backup(records, str(csv_path))

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert rows[0]["col"].startswith("'=")
