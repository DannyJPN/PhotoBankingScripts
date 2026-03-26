"""
Performance-oriented tests for filtering bank status records.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

from markphotomediaapprovalstatuslib.constants import BANKS, STATUS_CHECKED
from markphotomediaapprovalstatuslib.status_handler import filter_records_by_bank_status


def test_filter_records_by_bank_status_bulk():
    bank = BANKS[0]
    status_column = f"{bank} status"
    records = [{status_column: STATUS_CHECKED} for _ in range(400)]
    filtered = filter_records_by_bank_status(records, bank, STATUS_CHECKED)
    assert len(filtered) == 400
