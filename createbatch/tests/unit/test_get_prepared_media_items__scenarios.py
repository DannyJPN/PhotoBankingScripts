"""
Unit tests for get_prepared_media_items.
"""

import importlib
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

import createbatchlib.constants as constants


class DummyTqdm:
    def __init__(self, total, desc, unit):
        self.total = total
        self.desc = desc
        self.unit = unit

    def update(self, _count):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def import_module_fresh():
    sys.modules.pop("createbatchlib.get_prepared_media_items", None)
    return importlib.import_module("createbatchlib.get_prepared_media_items")


def test_get_prepared_media_items__missing_constant_import_error():
    if hasattr(constants, "PREPARED_STATUS"):
        delattr(constants, "PREPARED_STATUS")

    sys.modules.pop("createbatchlib.get_prepared_media_items", None)

    with pytest.raises(ImportError):
        importlib.import_module("createbatchlib.get_prepared_media_items")


def test_get_prepared_media_items__filters_prepared(monkeypatch):
    constants.PREPARED_STATUS = constants.PREPARED_STATUS_VALUE
    module = import_module_fresh()
    monkeypatch.setattr(module, "tqdm", DummyTqdm)

    items = [
        {"Cesta": "a.jpg", "Shutterstock Status": constants.PREPARED_STATUS},
        {"Cesta": "b.jpg", "Shutterstock Status": "ne" + constants.PREPARED_STATUS},
    ]

    result = module.get_prepared_media_items(items)

    assert result == [items[0]]


def test_get_prepared_media_items__value_error_exits(monkeypatch):
    constants.PREPARED_STATUS = constants.PREPARED_STATUS_VALUE
    module = import_module_fresh()
    monkeypatch.setattr(module, "tqdm", DummyTqdm)

    items = [{"Cesta": "a.jpg", "Shutterstock Status": None}]

    with pytest.raises(SystemExit) as excinfo:
        module.get_prepared_media_items(items)

    assert excinfo.value.code == 1
