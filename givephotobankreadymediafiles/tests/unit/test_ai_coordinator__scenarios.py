"""
Unit tests for givephotobankreadymediafileslib/ai_coordinator.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import ai_coordinator


class DummyCombo:
    def __init__(self, value=""):
        self._value = value
        self.values = None
        self.current_index = None

    def configure(self, values=None):
        self.values = values

    def set(self, value):
        self._value = value

    def get(self):
        return self._value

    def current(self, index):
        self.current_index = index


class DummyButton:
    def __init__(self):
        self.configs = []

    def configure(self, **kwargs):
        self.configs.append(kwargs)


class DummyEntry:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def delete(self, *_args):
        self.value = ""

    def insert(self, _index, value):
        self.value = value


class DummyText:
    def __init__(self, value=""):
        self.value = value

    def get(self, *_args):
        return self.value


class DummyVar:
    def __init__(self, value=False):
        self.value = value

    def get(self):
        return self.value


class DummyViewerState:
    def __init__(self):
        self.current_file_path = "C:/file.jpg"
        self.title_entry = DummyEntry("old")
        self.desc_text = DummyText("")
        self.editorial_var = DummyVar(False)
        self.keywords_list = []
        self.title_changed = False

    def on_title_change(self):
        self.title_changed = True


class DummyRoot:
    def after(self, _ms, func, *args):
        return func(*args)


class DummyAIThread:
    def __init__(self, alive=True):
        self._alive = alive

    def is_alive(self):
        return self._alive


def _build_coordinator(model_value="Model A"):
    viewer_state = DummyViewerState()
    ui = SimpleNamespace(
        model_combo=DummyCombo(model_value),
        title_generate_button=DummyButton(),
        desc_generate_button=DummyButton(),
        keywords_generate_button=DummyButton(),
        categories_generate_button=DummyButton(),
        generate_all_button=DummyButton(),
    )
    categories = SimpleNamespace(category_combos={})
    return ai_coordinator.AICoordinator(DummyRoot(), viewer_state, categories, ui)


def test_load_ai_models__no_models(monkeypatch):
    coordinator = _build_coordinator()

    class DummyConfig:
        def get_available_ai_models(self):
            return []

    import shared.config as shared_config

    monkeypatch.setattr(shared_config, "get_config", lambda: DummyConfig())
    coordinator.load_ai_models()
    assert coordinator.ui_components.model_combo.values == ["No models available"]


def test_load_ai_models__default_selection(monkeypatch):
    coordinator = _build_coordinator()

    models = [
        {"display_name": "Model A", "key": "p/a"},
        {"display_name": "Model B", "key": "p/b"},
    ]

    class DummyConfig:
        def get_available_ai_models(self):
            return models

        def get_default_ai_model(self):
            return ("p", "b")

    import shared.config as shared_config

    monkeypatch.setattr(shared_config, "get_config", lambda: DummyConfig())
    coordinator.load_ai_models()
    assert coordinator.ui_components.model_combo.current_index == 1


def test_get_current_ai_provider__invalid_model():
    coordinator = _build_coordinator(model_value="No models available")
    assert coordinator.get_current_ai_provider() is None


def test_get_current_ai_provider__success(monkeypatch):
    coordinator = _build_coordinator(model_value="Model A")

    class DummyConfig:
        def get_available_ai_models(self):
            return [{"display_name": "Model A", "key": "p/a"}]

    import shared.config as shared_config
    import shared.ai_factory as ai_factory

    monkeypatch.setattr(shared_config, "get_config", lambda: DummyConfig())
    monkeypatch.setattr(ai_factory, "create_from_model_key", lambda _k: "provider")

    assert coordinator.get_current_ai_provider() == "provider"


def test_generate_title__no_file(monkeypatch):
    coordinator = _build_coordinator()
    coordinator.viewer_state.current_file_path = ""
    called = []
    monkeypatch.setattr(ai_coordinator.messagebox, "showwarning", lambda *_a, **_k: called.append(True))

    coordinator.generate_title()
    assert called


def test_generate_title__invalid_model(monkeypatch):
    coordinator = _build_coordinator(model_value="No models available")
    called = []
    monkeypatch.setattr(ai_coordinator.messagebox, "showwarning", lambda *_a, **_k: called.append(True))

    coordinator.generate_title()
    assert called


def test_generate_title__cancel_running_thread(monkeypatch):
    coordinator = _build_coordinator()
    coordinator.ai_threads["title"] = DummyAIThread(alive=True)
    coordinator._generate_all_active = False

    coordinator.generate_title()
    assert coordinator.ai_cancelled["title"] is True
    assert coordinator.ai_threads["title"] is None


def test_update_title_result__stale_generation(monkeypatch):
    coordinator = _build_coordinator()
    coordinator.current_generation_id["title"] = 2
    coordinator._update_title_result("new", None, generation_id=1)
    assert coordinator.viewer_state.title_entry.get() == "old"


def test_update_title_result__error(monkeypatch):
    coordinator = _build_coordinator()
    coordinator.current_generation_id["title"] = 1
    called = []
    monkeypatch.setattr(ai_coordinator.messagebox, "showerror", lambda *_a, **_k: called.append(True))

    coordinator._update_title_result(None, "boom", generation_id=1)
    assert called


def test_update_title_result__success(monkeypatch):
    coordinator = _build_coordinator()
    coordinator.current_generation_id["title"] = 1

    coordinator._update_title_result("new title", None, generation_id=1)
    assert coordinator.viewer_state.title_entry.get() == "new title"
    assert coordinator.viewer_state.title_changed is True
