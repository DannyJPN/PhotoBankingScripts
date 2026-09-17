"""
Unit tests for uploadtophotobanks/shared/logging_config.py.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

import shared.logging_config as logging_config


def test_setup_logging__configures_handlers(monkeypatch):
    fake_json = io.StringIO('{"DEBUG":"white","INFO":"green","WARNING":"yellow","ERROR":"red","CRITICAL":"red"}')
    monkeypatch.setattr(logging_config, "open", lambda *_a, **_k: fake_json)

    class DummyFormatter:
        def __init__(self, *_a, **_k):
            return None

    class DummyHandler:
        def __init__(self, *_a, **_k):
            self.formatter = None

        def setFormatter(self, formatter):
            self.formatter = formatter

    monkeypatch.setattr(logging_config.colorlog, "ColoredFormatter", DummyFormatter)
    monkeypatch.setattr(logging_config.logging, "StreamHandler", lambda: DummyHandler())
    monkeypatch.setattr(logging_config.logging, "FileHandler", lambda *_a, **_k: DummyHandler())

    logging_config.setup_logging(debug=False, log_file="log.txt")
