"""
Unit tests for markphotomediaapprovalstatus.py.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

import markphotomediaapprovalstatus as mmp


def make_args(tmp_path, **overrides):
    defaults = dict(
        csv_path=str(tmp_path / "input.csv"),
        log_dir=str(tmp_path / "logs"),
        debug=False,
        include_edited=False,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_parse_arguments__defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["markphotomediaapprovalstatus.py"])
    args = mmp.parse_arguments()
    assert args.csv_path


def test_main__load_error_returns(monkeypatch, tmp_path):
    args = make_args(tmp_path)
    monkeypatch.setattr(mmp, "parse_arguments", lambda: args)
    monkeypatch.setattr(mmp, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(mmp, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(mmp, "setup_logging", lambda **_k: None)

    def fail_load(_p):
        raise OSError("fail")

    monkeypatch.setattr(mmp, "load_csv", fail_load)

    assert mmp.main() is None
