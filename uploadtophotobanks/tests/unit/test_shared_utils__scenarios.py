"""
Unit tests for uploadtophotobanks/shared/utils.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
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
