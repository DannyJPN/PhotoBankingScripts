"""
Performance-oriented tests for bank launcher CSV loading.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "launchphotobanks"
sys.path.insert(0, str(package_root))

from launchphotobankslib.bank_launcher import BankLauncher


def test_load_many_banks(tmp_path):
    csv_path = tmp_path / "banks.csv"
    rows = ["bank_name,url"]
    for i in range(200):
        rows.append(f"Bank{i},https://example.com/{i}")
    csv_path.write_text("\n".join(rows), encoding="utf-8")

    launcher = BankLauncher(str(csv_path))
    assert len(launcher.get_all_bank_names()) == 200
