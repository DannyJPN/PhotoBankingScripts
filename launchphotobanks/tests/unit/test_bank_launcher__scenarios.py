"""
Unit tests for launchphotobankslib/bank_launcher.py.
"""

import csv
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "launchphotobanks"
sys.path.insert(0, str(package_root))

from launchphotobankslib.bank_launcher import BankLauncher
from launchphotobankslib import constants as lp_constants


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_load_banks__valid_csv(tmp_path):
    csv_path = tmp_path / "banks.csv"
    write_csv(
        csv_path,
        [{"BankName": "TestBank", "URL": "https://example.com"}],
        ["BankName", "URL"],
    )

    launcher = BankLauncher(str(csv_path))

    assert launcher.get_all_bank_names() == ["TestBank"]
    assert launcher.get_bank_url("TestBank") == "https://example.com"


def test_load_banks__missing_header_raises(tmp_path):
    csv_path = tmp_path / "banks.csv"
    write_csv(csv_path, [{"Name": "A", "Link": "https://x"}], ["Name", "Link"])

    with pytest.raises(ValueError):
        BankLauncher(str(csv_path))


def test_load_banks__invalid_url_skipped(tmp_path):
    csv_path = tmp_path / "banks.csv"
    write_csv(
        csv_path,
        [{"BankName": "Bad", "URL": "notaurl"}],
        ["BankName", "URL"],
    )

    with pytest.raises(ValueError):
        BankLauncher(str(csv_path))


def test_is_valid_url():
    launcher = BankLauncher.__new__(BankLauncher)
    assert launcher._is_valid_url("https://example.com") is True
    assert launcher._is_valid_url("notaurl") is False


def test_launch_banks__unknown_bank_returns_false(tmp_path, monkeypatch):
    csv_path = tmp_path / "banks.csv"
    write_csv(
        csv_path,
        [{"BankName": "Known", "URL": "https://example.com"}],
        ["BankName", "URL"],
    )

    launcher = BankLauncher(str(csv_path))
    monkeypatch.setattr("webbrowser.open_new_tab", lambda _u: True)

    results = launcher.launch_banks(["Unknown"], delay=0)

    assert results["Unknown"] is False
