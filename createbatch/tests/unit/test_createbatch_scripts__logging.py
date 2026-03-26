"""
Unit tests for createbatch script logging setup.
"""

import importlib
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))


class DummyHandler:
    def __init__(self, *_args, **_kwargs):
        self.level = None
        self.formatter = None

    def setLevel(self, level):
        self.level = level

    def setFormatter(self, formatter):
        self.formatter = formatter


class DummyLogger:
    def __init__(self):
        self.level = None
        self.handlers = []

    def setLevel(self, level):
        self.level = level

    def addHandler(self, handler):
        self.handlers.append(handler)


def import_with_dummy_colorlog(module_name):
    class DummyColorlog:
        StreamHandler = DummyHandler

        class ColoredFormatter:
            def __init__(self, *_args, **_kwargs):
                return None

    sys.modules["colorlog"] = DummyColorlog
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def assert_setup_logging(module_name):
    module = import_with_dummy_colorlog(module_name)
    dummy_logger = DummyLogger()

    module.logging.getLogger = lambda: dummy_logger
    module.logging.FileHandler = DummyHandler

    logger = module.setup_logging()

    assert logger is dummy_logger
    assert len(dummy_logger.handlers) == 2


def test_export_prepared_media_setup_logging():
    assert_setup_logging("export_prepared_media")


def test_launch_photobanks_setup_logging():
    assert_setup_logging("launch_photobanks")


def test_mark_media_as_checked_setup_logging():
    assert_setup_logging("mark_media_as_checked")
