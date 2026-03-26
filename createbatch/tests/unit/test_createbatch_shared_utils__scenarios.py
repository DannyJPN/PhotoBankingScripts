"""
Unit tests for createbatch/shared/utils.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

import shared.utils as utils


def test_get_script_name__uses_argv_basename(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["C:/scripts/run_me.py"])

    assert utils.get_script_name() == "run_me"


def test_get_log_filename__includes_script_name_and_timestamp(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["C:/scripts/run_me.py"])

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
