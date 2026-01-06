"""
Unit tests for markmediaaschecked/shared modules.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

import shared.csv_handler as csv_handler
import shared.hash_utils as hash_utils
import shared.logging_config as logging_config
import shared.utils as utils


def test_csv_handler__import():
    assert callable(csv_handler.load_csv)


def test_hash_utils__md5(tmp_path):
    data_file = tmp_path / "data.bin"
    data_file.write_bytes(b"abc")
    assert len(hash_utils.compute_file_hash(str(data_file), method="md5")) == 32


def test_logging_config__missing_config_raises(monkeypatch):
    monkeypatch.setattr(logging_config, "open", lambda *_a, **_k: (_ for _ in ()).throw(OSError("missing")))
    with pytest.raises(Exception):
        logging_config.setup_logging()


def test_utils__get_log_filename(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["C:/tools/run_me.py"])

    class DummyDateTime:
        @classmethod
        def now(cls):
            class Dummy:
                def strftime(self, _fmt):
                    return "2020-01-01_12-00-00"

            return Dummy()

    monkeypatch.setattr(utils, "datetime", DummyDateTime)
    assert utils.get_log_filename("C:/logs").endswith("run_me_Log_2020-01-01_12-00-00.log")
