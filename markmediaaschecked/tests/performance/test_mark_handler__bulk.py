"""
Performance-oriented tests for mark handler updates.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

from markmediaascheckedlib.constants import STATUS_READY, STATUS_CHECKED
from markmediaascheckedlib.mark_handler import update_statuses


def test_update_statuses_bulk():
    records = [{"status_main": STATUS_READY} for _ in range(500)]
    count = update_statuses(records, ["status_main"])
    assert count == 500
    assert records[0]["status_main"] == STATUS_CHECKED
