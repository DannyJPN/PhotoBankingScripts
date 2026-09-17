"""
Unit tests for givephotobankreadymediafileslib/ui_components.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import ui_components


class DummyRoot:
    def __init__(self):
        self.after_calls = []
        self.cancel_calls = []

    def after(self, delay, callback):
        self.after_calls.append((delay, callback))
        return "timer-id"

    def after_cancel(self, timer_id):
        self.cancel_calls.append(timer_id)


class DummyWidget:
    def __init__(self, *args, **kwargs):
        self.bound = []

    def pack(self, *args, **kwargs):
        return None

    def add(self, *args, **kwargs):
        return None

    def bind(self, event, callback):
        self.bound.append((event, callback))


class DummyCombobox(DummyWidget):
    pass


class DummyButton(DummyWidget):
    pass


class DummyStyle:
    def __init__(self):
        self.configs = []

    def configure(self, name, **kwargs):
        self.configs.append((name, kwargs))


class DummyTtk:
    Style = DummyStyle
    Frame = DummyWidget
    Label = DummyWidget
    Button = DummyButton
    Combobox = DummyCombobox
    PanedWindow = DummyWidget
    LabelFrame = DummyWidget
    Scale = DummyWidget
    Checkbutton = DummyWidget


def test_setup_styles__configures_styles(monkeypatch):
    style = DummyStyle()

    class LocalTtk(DummyTtk):
        Style = lambda self=None: style

    monkeypatch.setattr(ui_components, "ttk", LocalTtk)
    ui = ui_components.UIComponents(root=DummyRoot())

    ui.setup_styles()
    assert style.configs


def test_setup_ui__delegates(monkeypatch):
    ui = ui_components.UIComponents(root=DummyRoot())
    calls = []

    monkeypatch.setattr(ui, "setup_media_panel", lambda *_a, **_k: calls.append("media"))
    monkeypatch.setattr(ui, "setup_metadata_panel", lambda *_a, **_k: calls.append("meta"))

    ui.setup_ui({}, {})
    assert calls == ["media", "meta"]


def test_setup_ai_model_panel__binds_selection(monkeypatch):
    monkeypatch.setattr(ui_components, "ttk", DummyTtk)
    ui = ui_components.UIComponents(root=DummyRoot())

    def on_select(_evt=None):
        return None

    ui.setup_ai_model_panel(DummyWidget(), on_select)
    assert isinstance(ui.model_combo, DummyCombobox)
    assert ui.model_combo.bound


def test_setup_categories_panel__creates_container(monkeypatch):
    monkeypatch.setattr(ui_components, "ttk", DummyTtk)
    ui = ui_components.UIComponents(root=DummyRoot())

    ui.setup_categories_panel(DummyWidget(), lambda: None)
    assert ui.categories_container is not None
    assert ui.categories_generate_button is not None


def test_update_all_button_states_debounced(monkeypatch):
    root = DummyRoot()
    ui = ui_components.UIComponents(root=root)

    called = []
    ui.set_button_update_callback(lambda: called.append(True))

    ui.update_all_button_states_debounced()
    assert root.after_calls

    ui._button_update_timer = "timer-id"
    ui.update_all_button_states_debounced()
    assert root.cancel_calls == ["timer-id"]


def test_set_button_update_callback():
    ui = ui_components.UIComponents(root=DummyRoot())
    callback = lambda: None
    ui.set_button_update_callback(callback)
    assert ui._button_update_callback is callback
