"""
Integration tests for launch_photo_banks dry-run path.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "launchphotobanks"
sys.path.insert(0, str(package_root))

import launch_photo_banks


def test_main_dry_run_uses_csv(tmp_path, monkeypatch):
    csv_path = tmp_path / "banks.csv"
    csv_path.write_text("bank_name,url\nBankA,https://example.com\n", encoding="utf-8")

    args = types.SimpleNamespace(
        bank_csv=str(csv_path),
        log_dir=str(tmp_path / "logs"),
        debug=False,
        delay=0,
        banks=None,
        dry_run=True,
    )

    monkeypatch.setattr(launch_photo_banks, "parse_arguments", lambda: args)
    monkeypatch.setattr(launch_photo_banks, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(launch_photo_banks, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(launch_photo_banks, "setup_logging", lambda **_k: None)

    assert launch_photo_banks.main() == 0
