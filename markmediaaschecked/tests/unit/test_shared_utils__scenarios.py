"""
Unit tests for markmediaaschecked/shared/utils.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

import shared.utils as utils


def test_get_script_name__uses_argv(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["C:/tools/run_me.py"])
    assert utils.get_script_name() == "run_me"


def test_get_log_filename__formats(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["C:/tools/run_me.py"])

    class DummyDateTime:
        @classmethod
        def now(cls):
            class Dummy:
                def strftime(self, _fmt):
                    return "2020-01-01_12-00-00"

            return Dummy()

    monkeypatch.setattr(utils, "datetime", DummyDateTime)
    result = utils.get_log_filename("C:/logs")
    assert result.endswith("run_me_Log_2020-01-01_12-00-00.log")


def test_detect_encoding__uses_chardet(monkeypatch, tmp_path):
    file_path = tmp_path / "data.txt"
    file_path.write_bytes(b"abc")

    monkeypatch.setattr(utils.chardet, "detect", lambda _data: {"encoding": "utf-8"})
    assert utils.detect_encoding(str(file_path)) == "utf-8"
