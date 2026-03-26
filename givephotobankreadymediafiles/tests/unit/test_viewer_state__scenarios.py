"""
Unit tests for givephotobankreadymediafileslib/viewer_state.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import viewer_state
from givephotobankreadymediafileslib import constants


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
        self.focused = False

    def get(self, *_args):
        return self.value

    def delete(self, *_args):
        self.value = ""

    def insert(self, _index, value):
        self.value = value

    def focus(self):
        self.focused = True


class DummyLabel:
    def __init__(self):
        self.text = None
        self.foreground = None

    def configure(self, **kwargs):
        self.text = kwargs.get("text", self.text)
        self.foreground = kwargs.get("foreground", self.foreground)


class DummyVar:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class DummyTagEntry:
    def __init__(self, tags=None):
        self.tags = tags or []
        self.set_calls = []

    def get_tags(self):
        return self.tags

    def set_tags(self, tags):
        self.set_calls.append(tags)


def test_on_title_change__truncates_and_colors():
    state = viewer_state.ViewerState(root=object())
    state.title_entry = DummyEntry("x" * (constants.MAX_TITLE_LENGTH + 2))
    state.title_char_label = DummyLabel()

    state.on_title_change()
    assert len(state.title_entry.get()) == constants.MAX_TITLE_LENGTH
    assert state.title_char_label.foreground == "red"


def test_on_description_change__truncates_and_colors():
    state = viewer_state.ViewerState(root=object())
    state.desc_text = DummyText("x" * (constants.MAX_DESCRIPTION_LENGTH + 2))
    state.desc_char_label = DummyLabel()

    state.on_description_change()
    assert len(state.desc_text.get()) == constants.MAX_DESCRIPTION_LENGTH
    assert state.desc_char_label.foreground == "red"


def test_focus_out_triggers_callback():
    state = viewer_state.ViewerState(root=object())
    called = []
    state.update_button_states_callback = lambda: called.append(True)

    state.on_title_focus_out()
    state.on_description_focus_out()
    state.on_keywords_focus_out()
    assert len(called) == 3


def test_keywords_change_and_refresh():
    state = viewer_state.ViewerState(root=object())
    state.keywords_tag_entry = DummyTagEntry(tags=["one", "two"])
    state.on_keywords_change()
    assert state.keywords_list == ["one", "two"]

    state.keywords_list = ["three"]
    state.refresh_keywords_display()
    assert state.keywords_tag_entry.set_calls == [["three"]]


def test_handle_title_input_moves_focus():
    state = viewer_state.ViewerState(root=object())
    state.desc_text = DummyText()
    state.handle_title_input(None)
    assert state.desc_text.focused is True


def test_load_metadata_from_record_and_collect():
    state = viewer_state.ViewerState(root=object())
    state.title_entry = DummyEntry()
    state.desc_text = DummyText()
    state.title_char_label = DummyLabel()
    state.desc_char_label = DummyLabel()
    state.keywords_tag_entry = DummyTagEntry()
    state.editorial_var = DummyVar()

    record = {
        constants.COL_TITLE: "Title",
        constants.COL_DESCRIPTION: "Desc",
        constants.COL_KEYWORDS: "one, two",
        constants.COL_EDITORIAL: "yes",
    }
    state.load_metadata_from_record(record)

    assert state.title_entry.get() == "Title"
    assert state.desc_text.get() == "Desc"
    assert state.keywords_list == ["one", "two"]
    assert state.editorial_var.get() is True

    collected = state.collect_metadata()
    assert collected["title"] == "Title"
    assert collected["editorial"] is True


def test_collect_metadata__missing_widgets():
    state = viewer_state.ViewerState(root=object())
    assert state.collect_metadata() == {}
