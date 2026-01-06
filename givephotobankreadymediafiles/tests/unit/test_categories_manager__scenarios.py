"""
Unit tests for givephotobankreadymediafileslib/categories_manager.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import categories_manager


class DummyFrame:
    def __init__(self, *_args, **_kwargs):
        self.packed = False

    def pack(self, *_args, **_kwargs):
        self.packed = True


class DummyLabel:
    def __init__(self, *_args, **_kwargs):
        self.text = _kwargs.get("text", "")

    def pack(self, *_args, **_kwargs):
        return None


class DummyCombobox:
    def __init__(self, *_args, **kwargs):
        self._values = kwargs.get("values", [])
        self._value = ""

    def pack(self, *_args, **_kwargs):
        return None

    def set(self, value):
        self._value = value

    def get(self):
        return self._value

    def __getitem__(self, key):
        if key == "values":
            return self._values
        raise KeyError(key)


class DummyTtk:
    Frame = DummyFrame
    Label = DummyLabel
    Combobox = DummyCombobox


def test_populate_categories_ui__no_container(monkeypatch):
    monkeypatch.setattr(categories_manager, "ttk", DummyTtk)
    manager = categories_manager.CategoriesManager(root=object(), categories={"ShutterStock": ["A"]})

    manager.populate_categories_ui()
    assert manager.category_combos == {}


def test_populate_categories_ui__creates_dropdowns(monkeypatch):
    monkeypatch.setattr(categories_manager, "ttk", DummyTtk)
    manager = categories_manager.CategoriesManager(root=object(), categories={"ShutterStock": ["A", "B"]})
    manager.categories_container = DummyFrame()

    manager.populate_categories_ui()

    assert "ShutterStock" in manager.category_combos
    assert len(manager.category_combos["ShutterStock"]) == 2


def test_load_collect_update_categories(monkeypatch):
    monkeypatch.setattr(categories_manager, "ttk", DummyTtk)
    manager = categories_manager.CategoriesManager(root=object(), categories={"ShutterStock": ["A", "B"]})
    manager.categories_container = DummyFrame()
    manager.populate_categories_ui()

    record = {"ShutterStock kategorie": "A, B"}
    manager.load_existing_categories(record)

    selected = manager.collect_selected_categories()
    assert selected["ShutterStock"] == ["A", "B"]

    manager.update_categories({"ShutterStock": ["B"]})
    selected_after = manager.collect_selected_categories()
    assert selected_after["ShutterStock"][0] == "B"
