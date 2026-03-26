"""
Unit tests for givephotobankreadymediafileslib/metadata_validator.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import metadata_validator


class DummyEntry:
    def __init__(self, value=""):
        self._value = value

    def get(self):
        return self._value


class DummyText:
    def __init__(self, value=""):
        self._value = value

    def get(self, *_args):
        return self._value


class DummyButton:
    def __init__(self):
        self.state = "disabled"

    def configure(self, state=None, **_kwargs):
        if state is not None:
            self.state = state

    def __getitem__(self, key):
        if key == "state":
            return self.state
        raise KeyError(key)


class DummyLock:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


class DummyModelCombo:
    def __init__(self, value=""):
        self._value = value

    def get(self):
        return self._value


class DummyAIProvider:
    def __init__(self, can_generate=True):
        self._can_generate = can_generate

    def can_generate_with_inputs(self, has_image, has_text):
        return self._can_generate and (has_image or has_text)


class DummyViewerState:
    def __init__(self, file_path=None, title="", desc="", keywords=None):
        self.current_file_path = file_path
        self.title_entry = DummyEntry(title)
        self.desc_text = DummyText(desc)
        self.keywords_list = keywords or []


class DummyAI:
    def __init__(self, provider=None):
        self._provider = provider
        self.generation_lock = DummyLock()
        self.ai_threads = {}

    def get_current_ai_provider(self):
        return self._provider


class DummyUI:
    def __init__(self):
        self.model_combo = DummyModelCombo()
        self.title_generate_button = DummyButton()
        self.desc_generate_button = DummyButton()
        self.keywords_generate_button = DummyButton()
        self.categories_generate_button = DummyButton()
        self.generate_all_button = DummyButton()


def test_check_available_inputs__fields(monkeypatch):
    monkeypatch.setattr(metadata_validator.os.path, "exists", lambda _p: True)
    viewer_state = DummyViewerState(file_path="C:/file.jpg", title="t", desc="d", keywords=["k"])
    validator = metadata_validator.MetadataValidator(viewer_state, DummyUI(), DummyAI(), object())

    assert validator.check_available_inputs("title") == {"has_image": True, "has_text": True}
    assert validator.check_available_inputs("description") == {"has_image": True, "has_text": True}
    assert validator.check_available_inputs("keywords") == {"has_image": True, "has_text": True}
    assert validator.check_available_inputs("categories") == {"has_image": True, "has_text": True}


def test_should_enable_generation_button__no_file():
    viewer_state = DummyViewerState(file_path=None)
    validator = metadata_validator.MetadataValidator(viewer_state, DummyUI(), DummyAI(), object())

    assert validator.should_enable_generation_button("title") is False


def test_should_enable_generation_button__provider_can_generate(monkeypatch):
    monkeypatch.setattr(metadata_validator.os.path, "exists", lambda _p: True)
    viewer_state = DummyViewerState(file_path="C:/file.jpg", title="title")
    provider = DummyAIProvider(can_generate=True)
    validator = metadata_validator.MetadataValidator(viewer_state, DummyUI(), DummyAI(provider), object())

    assert validator.should_enable_generation_button("title", ai_provider=provider) is True


def test_should_enable_generation_button__provider_missing(monkeypatch):
    monkeypatch.setattr(metadata_validator.os.path, "exists", lambda _p: True)

    class DummyConfig:
        def get_default_ai_model(self):
            return ("provider", "model")

    import shared.config as shared_config

    monkeypatch.setattr(shared_config, "get_config", lambda: DummyConfig())
    viewer_state = DummyViewerState(file_path="C:/file.jpg")
    ui = DummyUI()
    validator = metadata_validator.MetadataValidator(viewer_state, ui, DummyAI(provider=None), object())

    assert validator.should_enable_generation_button("title") is False


def test_update_all_button_states__enables_when_any(monkeypatch):
    monkeypatch.setattr(metadata_validator.os.path, "exists", lambda _p: True)
    viewer_state = DummyViewerState(file_path="C:/file.jpg", title="title")
    provider = DummyAIProvider(can_generate=True)
    ui = DummyUI()
    validator = metadata_validator.MetadataValidator(viewer_state, ui, DummyAI(provider), object())

    validator.update_all_button_states()
    assert ui.generate_all_button.state == "normal"


def test_update_button_state__skips_when_thread_alive(monkeypatch):
    monkeypatch.setattr(metadata_validator.os.path, "exists", lambda _p: True)
    viewer_state = DummyViewerState(file_path="C:/file.jpg", title="title")
    provider = DummyAIProvider(can_generate=True)
    ui = DummyUI()
    ai = DummyAI(provider)

    class DummyThread:
        def is_alive(self):
            return True

    ai.ai_threads["title"] = DummyThread()
    validator = metadata_validator.MetadataValidator(viewer_state, ui, ai, object())

    ui.title_generate_button.state = "disabled"
    validator.update_button_state("title", ui.title_generate_button, provider)
    assert ui.title_generate_button.state == "disabled"
