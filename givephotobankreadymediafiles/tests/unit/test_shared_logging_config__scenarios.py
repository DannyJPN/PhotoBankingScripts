"""
Unit tests for givephotobankreadymediafiles/shared/logging_config.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

import shared.logging_config as logging_config


class DummyHandler:
    def __init__(self, *_args, **_kwargs):
        self.formatter = None

    def setFormatter(self, formatter):
        self.formatter = formatter


class DummyLogger:
    def __init__(self):
        self.handlers = [DummyHandler()]
        self.level = None

    def setLevel(self, level):
        self.level = level

    def addHandler(self, handler):
        self.handlers.append(handler)

    def removeHandler(self, handler):
        self.handlers.remove(handler)


class DummyFormatter:
    def __init__(self, *_args, **_kwargs):
        return None


def test_setup_logging__missing_config_raises(monkeypatch):
    def fail_open(*_args, **_kwargs):
        raise OSError("missing")

    monkeypatch.setattr(logging_config, "open", fail_open)

    with pytest.raises(Exception):
        logging_config.setup_logging()


def test_setup_logging__sets_level_and_handlers(monkeypatch):
    dummy_logger = DummyLogger()

    monkeypatch.setattr(logging_config.logging, "getLogger", lambda: dummy_logger)
    monkeypatch.setattr(logging_config.logging, "StreamHandler", DummyHandler)
    monkeypatch.setattr(logging_config.logging, "FileHandler", DummyHandler)
    monkeypatch.setattr(logging_config.colorlog, "ColoredFormatter", DummyFormatter)

    def fake_open(*_args, **_kwargs):
        class DummyFile:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return '{"DEBUG": "white", "INFO": "green", "WARNING": "yellow", "ERROR": "red", "CRITICAL": "red"}'

        return DummyFile()

    monkeypatch.setattr(logging_config, "open", fake_open)
    monkeypatch.setattr(logging_config.json, "load", lambda _f: {
        "DEBUG": "white",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red",
    })

    logging_config.setup_logging(debug=False, log_file="C:/logs/test.log")

    assert dummy_logger.level == logging_config.logging.INFO
    assert len(dummy_logger.handlers) == 2
