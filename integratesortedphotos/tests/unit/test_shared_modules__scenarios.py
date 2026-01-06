"""
Unit tests for integratesortedphotos/shared modules.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "integratesortedphotos"
sys.path.insert(0, str(package_root))

from shared import utils as shared_utils


def test_utils__get_log_filename(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["C:/tools/run_me.py"])

    class DummyDateTime:
        @classmethod
        def now(cls):
            class Dummy:
                def strftime(self, _fmt):
                    return "2020-01-01_12-00-00"

            return Dummy()

    monkeypatch.setattr(shared_utils, "datetime", DummyDateTime)
    result = shared_utils.get_log_filename("C:/logs")
    assert result.endswith("run_me_Log_2020-01-01_12-00-00.log")
