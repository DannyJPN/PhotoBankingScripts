"""
Security-focused tests for URL validation in bank launcher.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "launchphotobanks"
sys.path.insert(0, str(package_root))

from launchphotobankslib.bank_launcher import BankLauncher


def test_rejects_javascript_urls(tmp_path):
    csv_path = tmp_path / "banks.csv"
    csv_path.write_text(
        "bank_name,url\nBad,javascript:alert(1)\nGood,https://example.com\n",
        encoding="utf-8",
    )

    launcher = BankLauncher(str(csv_path))
    banks = launcher.get_all_bank_names()
    assert banks == ["Good"]
