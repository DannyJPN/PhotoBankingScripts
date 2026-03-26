"""
Security-focused tests for handling missing files in approval workflow.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

from markphotomediaapprovalstatuslib.constants import BANKS, STATUS_CHECKED
from markphotomediaapprovalstatuslib.media_helper import process_approval_records


def test_process_approval_records_skips_missing_files(monkeypatch):
    bank = BANKS[0]
    status_column = f"{bank} status"

    record = {"Soubor": "missing.jpg", "Cesta": "X:/missing.jpg", status_column: STATUS_CHECKED}
    data = [record]

    saved = {"count": 0}
    monkeypatch.setattr(
        "markphotomediaapprovalstatuslib.media_helper.save_csv_with_backup",
        lambda *_a, **_k: saved.__setitem__("count", saved["count"] + 1),
    )
    monkeypatch.setattr(
        "markphotomediaapprovalstatuslib.media_helper.os.path.exists",
        lambda _p: False,
    )

    changed = process_approval_records(data, data, "out.csv")
    assert changed is False
    assert saved["count"] == 0
