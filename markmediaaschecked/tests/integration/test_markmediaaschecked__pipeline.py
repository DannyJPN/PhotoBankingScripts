"""
Integration tests for markmediaaschecked end-to-end flow.
"""

import csv
import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

import markmediaaschecked
from markmediaascheckedlib.constants import STATUS_READY, STATUS_CHECKED


def _write_csv(path: Path, records):
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def test_main_updates_status_and_creates_backup(tmp_path, monkeypatch):
    csv_path = tmp_path / "photos.csv"
    records = [
        {"status_main": STATUS_READY, "Soubor": "img1.jpg", "Cesta": "x"},
        {"status_main": "other", "Soubor": "img2.jpg", "Cesta": "x"},
    ]
    _write_csv(csv_path, records)

    args = types.SimpleNamespace(
        photo_csv_file=str(csv_path),
        overwrite=True,
        debug=False,
        log_dir=str(tmp_path / "logs"),
        include_edited=False,
    )

    monkeypatch.setattr(markmediaaschecked, "parse_arguments", lambda: args)
    monkeypatch.setattr(markmediaaschecked, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(markmediaaschecked, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(markmediaaschecked, "get_log_filename", lambda _p: "log.txt")

    markmediaaschecked.main()

    backup_files = list(tmp_path.glob("photos.csv.*.old"))
    assert backup_files

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert rows[0]["status_main"] == STATUS_CHECKED
