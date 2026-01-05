"""
Unit tests for givephotobankreadymediafileslib/tag_entry.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import tag_entry


class DummyButton:
    def __init__(self):
        self.state = "disabled"
        self.text = None
        self.command = None

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]
        if "text" in kwargs:
            self.text = kwargs["text"]
        if "command" in kwargs:
            self.command = kwargs["command"]


class DummyLabel:
    def __init__(self):
        self.text = None
        self.foreground = None

    def configure(self, **kwargs):
        self.text = kwargs.get("text", self.text)
        self.foreground = kwargs.get("foreground", self.foreground)


class DummyEntry:
    def __init__(self):
        self.text = ""
        self.state = "disabled"
        self.focused = False

    def configure(self, state=None):
        if state is not None:
            self.state = state

    def delete(self, *_args):
        self.text = ""

    def insert(self, _index, value):
        self.text = value

    def get(self):
        return self.text

    def focus(self):
        self.focused = True

    def select_range(self, *_args):
        return None

    def __getitem__(self, key):
        if key == "state":
            return self.state
        raise KeyError(key)


class DummyListbox:
    def __init__(self):
        self.items = []
        self.selection = ()
        self._nearest = 0

    def curselection(self):
        return self.selection

    def selection_clear(self, *_args):
        self.selection = ()

    def selection_set(self, index):
        self.selection = (index,)

    def delete(self, *_args):
        self.items = []

    def insert(self, _pos, text):
        self.items.append(text)

    def nearest(self, _y):
        return self._nearest

    def set_nearest(self, value):
        self._nearest = value


def _build_entry():
    entry = tag_entry.TagEntry.__new__(tag_entry.TagEntry)
    entry.max_tags = 5
    entry.separators = set(",;")
    entry.on_change = None
    entry._tags = []
    entry._edit_mode = False
    entry._edit_index = None
    entry.listbox = DummyListbox()
    entry.entry = DummyEntry()
    entry.up_button = DummyButton()
    entry.down_button = DummyButton()
    entry.top_button = DummyButton()
    entry.bottom_button = DummyButton()
    entry.edit_button = DummyButton()
    entry.delete_button = DummyButton()
    entry.clear_button = DummyButton()
    entry.add_button = DummyButton()
    entry.counter_label = DummyLabel()
    return entry


def test_update_button_states__selection():
    entry = _build_entry()
    entry._tags = ["a", "b"]
    entry.listbox.selection_set(0)

    entry.update_button_states()
    assert entry.up_button.state == "disabled"
    assert entry.down_button.state == "normal"
    assert entry.clear_button.state == "normal"


def test_add_and_remove_tags():
    entry = _build_entry()
    assert entry.add_tag("tag1") is True
    assert entry.add_tag("ta") is True
    assert entry.add_tag("ta") is False
    assert entry.get_tags() == ["tag1", "ta"]

    entry.listbox.selection_set(0)
    entry.remove_selected_tags()
    assert entry.get_tags() == ["ta"]


def test_set_and_clear_tags():
    entry = _build_entry()
    entry.set_tags(["a", "bb", "ccc"])
    assert entry.get_tags() == ["bb", "ccc"]

    entry.clear_tags()
    assert entry.get_tags() == []


def test_focus__starts_add_mode():
    entry = _build_entry()
    entry.focus()
    assert entry.entry.state == "normal"


def test_get_set_text():
    entry = _build_entry()
    entry.set_text("one, two")
    assert entry.get_text() == "one, two"

    entry.set_text("")
    assert entry.get_tags() == []


def test_start_and_cancel_add_mode():
    entry = _build_entry()
    entry.start_add_mode()
    assert entry.entry.state == "normal"
    assert entry.add_button.text == "Confirm"

    entry.cancel_entry_mode()
    assert entry.entry.state == "disabled"
    assert entry.add_button.text == "Add"


def test_start_edit_mode_and_confirm():
    entry = _build_entry()
    entry._tags = ["first", "second"]
    entry.listbox.selection_set(1)

    entry.start_edit_mode()
    assert entry._edit_mode is True
    assert entry.entry.get() == "second"

    entry.entry.text = "updated"
    entry.confirm_edit()
    assert entry._tags[1] == "updated"


def test_confirm_add__multiple_tags():
    entry = _build_entry()
    entry.start_add_mode()
    entry.entry.text = "alpha, beta; gamma"
    entry.confirm_add()
    assert entry.get_tags() == ["alpha", "beta", "gamma"]


def test_move_up_down_top_bottom():
    entry = _build_entry()
    entry._tags = ["a", "b", "c"]
    entry.listbox.selection_set(1)

    entry.move_up()
    assert entry._tags == ["b", "a", "c"]

    entry.listbox.selection_set(1)
    entry.move_down()
    assert entry._tags == ["b", "c", "a"]

    entry.listbox.selection_set(2)
    entry.move_to_top()
    assert entry._tags[0] == "a"

    entry.listbox.selection_set(0)
    entry.move_to_bottom()
    assert entry._tags[-1] == "a"


def test_on_click__cancels_entry_mode():
    entry = _build_entry()
    entry._tags = ["a", "b"]
    entry.entry.state = "normal"

    called = []
    entry.cancel_entry_mode = lambda *_a, **_k: called.append(True)

    entry.listbox.set_nearest(1)
    entry.on_click(type("Evt", (), {"y": 0})())
    assert called
