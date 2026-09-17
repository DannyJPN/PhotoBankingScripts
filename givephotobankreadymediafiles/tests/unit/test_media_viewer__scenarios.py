"""
Unit tests for givephotobankreadymediafileslib/media_viewer.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import media_viewer


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
        self.foreground = None
        self.focused = False

    def get(self, *_args):
        return self.value

    def delete(self, *_args):
        self.value = ""

    def insert(self, _index, value):
        self.value = value

    def config(self, **kwargs):
        self.foreground = kwargs.get("foreground", self.foreground)

    def focus(self):
        self.focused = True


class DummyLabel:
    def __init__(self):
        self.text = None
        self.foreground = None

    def configure(self, **kwargs):
        self.text = kwargs.get("text", self.text)
        self.foreground = kwargs.get("foreground", self.foreground)


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


class DummyModelCombo:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value


class DummyAIProvider:
    def __init__(self, can_generate=True):
        self.can_generate = can_generate

    def can_generate_with_inputs(self, has_image, has_text):
        return self.can_generate and (has_image or has_text)


def _build_viewer():
    viewer = media_viewer.MediaViewer.__new__(media_viewer.MediaViewer)
    viewer.user_desc_placeholder = "placeholder"
    viewer.user_desc_text = DummyText("placeholder")
    viewer.title_entry = DummyEntry()
    viewer.desc_text = DummyText()
    viewer.title_char_label = DummyLabel()
    viewer.desc_char_label = DummyLabel()
    viewer.keywords_tag_entry = type("DummyTag", (), {"get_tags": lambda _s: ["one", "two"], "set_tags": lambda _s, _t: None})()
    viewer.keywords_list = []
    viewer.keywords_count_label = DummyLabel()
    viewer._button_update_timer = None
    viewer.root = type("DummyRoot", (), {"after_cancel": lambda *_a, **_k: None, "after": lambda *_a, **_k: "timer"})()
    viewer.ai_threads = {"title": None}
    viewer.title_generate_button = DummyButton()
    viewer.desc_generate_button = DummyButton()
    viewer.keywords_generate_button = DummyButton()
    viewer.categories_generate_button = DummyButton()
    viewer.generate_all_button = DummyButton()
    viewer.model_combo = DummyModelCombo()
    return viewer


def test_user_desc_placeholder_focus_in_out():
    viewer = _build_viewer()
    viewer.on_user_desc_focus_in()
    assert viewer.user_desc_text.value == ""
    assert viewer.user_desc_text.foreground == "black"

    viewer.on_user_desc_focus_out()
    assert viewer.user_desc_text.value == "placeholder"
    assert viewer.user_desc_text.foreground == "gray"


def test_get_user_description():
    viewer = _build_viewer()
    assert viewer.get_user_description() is None
    viewer.user_desc_text.value = "Real text"
    assert viewer.get_user_description() == "Real text"


def test_title_and_description_change_truncates():
    viewer = _build_viewer()
    viewer.title_entry.value = "x" * (media_viewer.MAX_TITLE_LENGTH + 1)
    viewer.on_title_change()
    assert len(viewer.title_entry.get()) == media_viewer.MAX_TITLE_LENGTH

    viewer.desc_text.value = "x" * (media_viewer.MAX_DESCRIPTION_LENGTH + 1)
    viewer.on_description_change()
    assert len(viewer.desc_text.get()) == media_viewer.MAX_DESCRIPTION_LENGTH


def test_keywords_change_updates_counter():
    viewer = _build_viewer()
    viewer.on_keywords_change()
    assert viewer.keywords_list == ["one", "two"]
    assert viewer.keywords_count_label.text == "2/50"


def test_update_all_button_states_debounced():
    viewer = _build_viewer()
    calls = []
    viewer.root.after = lambda *_a, **_k: calls.append(True) or "timer"

    viewer.update_all_button_states_debounced()
    assert calls


def test_check_available_inputs(monkeypatch):
    viewer = _build_viewer()
    viewer.current_file_path = "C:/file.jpg"
    monkeypatch.setattr(media_viewer.os.path, "exists", lambda _p: True)
    viewer.title_entry.value = "title"
    inputs = viewer.check_available_inputs("title")
    assert inputs["has_image"] is True
    assert inputs["has_text"] is True


def test_should_enable_generation_button__no_file():
    viewer = _build_viewer()
    viewer.current_file_path = None
    assert viewer.should_enable_generation_button("title") is False


def test_should_enable_generation_button__provider():
    viewer = _build_viewer()
    viewer.current_file_path = "C:/file.jpg"
    provider = DummyAIProvider(can_generate=True)
    assert viewer.should_enable_generation_button("title", provider) is True


def test_update_button_state__thread_alive(monkeypatch):
    viewer = _build_viewer()

    class DummyThread:
        def is_alive(self):
            return True

    viewer.ai_threads["title"] = DummyThread()
    viewer.update_button_state("title", viewer.title_generate_button, DummyAIProvider())
    assert viewer.title_generate_button.state == "disabled"
