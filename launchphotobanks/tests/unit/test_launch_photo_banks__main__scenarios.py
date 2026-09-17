"""
Unit tests for launch_photo_banks.py.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "launchphotobanks"
sys.path.insert(0, str(package_root))

import launch_photo_banks as launch_module
from launchphotobankslib import constants as lp_constants


def make_args(tmp_path, **overrides):
    defaults = dict(
        bank_csv=str(tmp_path / "banks.csv"),
        log_dir=str(tmp_path / "logs"),
        debug=False,
        delay=lp_constants.DEFAULT_DELAY_BETWEEN_OPENS,
        banks=None,
        dry_run=False,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_parse_arguments__defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["launch_photo_banks.py"])
    args = launch_module.parse_arguments()

    assert args.bank_csv == lp_constants.DEFAULT_BANK_CSV
    assert args.log_dir == lp_constants.DEFAULT_LOG_DIR
    assert args.delay == lp_constants.DEFAULT_DELAY_BETWEEN_OPENS


def test_main__invalid_banks_returns_error(monkeypatch, tmp_path):
    args = make_args(tmp_path, banks=["Unknown"])
    monkeypatch.setattr(launch_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(launch_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(launch_module, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(launch_module, "setup_logging", lambda **_k: None)

    class DummyLauncher:
        def __init__(self, _path):
            pass

        def get_all_bank_names(self):
            return ["Known"]

        def get_bank_url(self, bank):
            return f"http://{bank}.test"

    monkeypatch.setattr(launch_module, "BankLauncher", DummyLauncher)

    assert launch_module.main() == 1


def test_main__dry_run(monkeypatch, tmp_path):
    args = make_args(tmp_path, banks=["BankA"], dry_run=True)
    monkeypatch.setattr(launch_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(launch_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(launch_module, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(launch_module, "setup_logging", lambda **_k: None)

    class DummyLauncher:
        def __init__(self, _path):
            pass

        def get_all_bank_names(self):
            return ["BankA"]

        def get_bank_url(self, bank):
            return f"http://{bank}.test"

    monkeypatch.setattr(launch_module, "BankLauncher", DummyLauncher)

    assert launch_module.main() == 0
