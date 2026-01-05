"""
Integration tests for process_approval_records workflow.
"""

import sys
import types
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

from markphotomediaapprovalstatuslib.constants import BANKS, STATUS_CHECKED, STATUS_APPROVED
from markphotomediaapprovalstatuslib.media_helper import process_approval_records


def test_process_approval_records_updates_and_saves(tmp_path, monkeypatch):
    media_path = tmp_path / "photo.jpg"
    media_path.write_bytes(b"data")

    bank = BANKS[0]
    status_column = f"{bank} status"

    record = {"Soubor": "photo.jpg", "Cesta": str(media_path), status_column: STATUS_CHECKED}
    data = [record]

    saved = {"count": 0}

    def fake_show_media_viewer(_path, _record, callback, target_bank):
        assert target_bank == bank
        callback(STATUS_APPROVED)

    monkeypatch.setattr(
        "markphotomediaapprovalstatuslib.media_helper.save_csv_with_backup",
        lambda *_a, **_k: saved.__setitem__("count", saved["count"] + 1),
    )
    monkeypatch.setattr(
        "markphotomediaapprovalstatuslib.media_helper.os.path.exists",
        lambda _p: True,
    )
    dummy_viewer = types.SimpleNamespace(show_media_viewer=fake_show_media_viewer)
    monkeypatch.setitem(sys.modules, "markphotomediaapprovalstatuslib.media_viewer", dummy_viewer)

    changed = process_approval_records(data, data, str(tmp_path / "out.csv"))
    assert changed is True
    assert record[status_column] == STATUS_APPROVED
    assert saved["count"] == 1
