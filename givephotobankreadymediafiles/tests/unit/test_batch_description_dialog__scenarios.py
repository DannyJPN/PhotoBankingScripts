"""
Unit tests for givephotobankreadymediafileslib/batch_description_dialog.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import batch_description_dialog


class DummyText:
    def __init__(self, value=""):
        self.value = value

    def get(self, *_args):
        return self.value


class DummyLabel:
    def __init__(self):
        self.text = None

    def configure(self, **kwargs):
        self.text = kwargs.get("text")


class DummyButton:
    def __init__(self):
        self.states = []

    def state(self, value):
        self.states.append(value)


class DummyVar:
    def __init__(self, value=False):
        self._value = value

    def get(self):
        return self._value


class DummyParent:
    def __init__(self):
        self.destroyed = False

    def destroy(self):
        self.destroyed = True


def _build_dialog(min_length=5, description="text", editorial=False):
    dialog = batch_description_dialog.BatchDescriptionDialog.__new__(batch_description_dialog.BatchDescriptionDialog)
    dialog.parent = DummyParent()
    dialog.file_path = "C:/file.jpg"
    dialog.min_length = min_length
    dialog.progress_text = ""
    dialog.saved_count = 0
    dialog.batch_limit = 20
    dialog.result = None
    dialog.desc_text = DummyText(description)
    dialog.counter_label = DummyLabel()
    dialog.save_button = DummyButton()
    dialog.editorial_var = DummyVar(editorial)
    return dialog


def test_update_counter__enables_when_length_ok():
    dialog = _build_dialog(min_length=3, description="abcd")
    dialog._update_counter()
    assert ["!disabled"] in dialog.save_button.states


def test_on_save__too_short(monkeypatch):
    dialog = _build_dialog(min_length=10, description="short")
    called = []
    monkeypatch.setattr(batch_description_dialog.messagebox, "showwarning", lambda *_a, **_k: called.append(True))

    dialog._on_save()
    assert called
    assert dialog.result is None


def test_on_save__editorial_cancel(monkeypatch):
    dialog = _build_dialog(min_length=1, description="long enough", editorial=True)
    monkeypatch.setattr(batch_description_dialog, "extract_editorial_metadata_from_exif", lambda _p: ({}, {}))
    monkeypatch.setattr(batch_description_dialog, "get_editorial_metadata", lambda *_a, **_k: None)

    dialog._on_save()
    assert dialog.result is None


def test_on_save__success(monkeypatch):
    dialog = _build_dialog(min_length=1, description="long enough", editorial=False)
    monkeypatch.setattr(batch_description_dialog, "extract_editorial_metadata_from_exif", lambda _p: ({}, {}))

    dialog._on_save()
    assert dialog.result["action"] == "save"
    assert dialog.parent.destroyed is True


def test_on_reject__confirmation_false(monkeypatch):
    dialog = _build_dialog()
    monkeypatch.setattr(batch_description_dialog.messagebox, "askyesno", lambda *_a, **_k: False)

    dialog._on_reject()
    assert dialog.result is None


def test_on_reject__confirmation_true(monkeypatch):
    dialog = _build_dialog()
    monkeypatch.setattr(batch_description_dialog.messagebox, "askyesno", lambda *_a, **_k: True)

    dialog._on_reject()
    assert dialog.result == {"action": "reject"}
    assert dialog.parent.destroyed is True


def test_on_skip_and_cancel():
    dialog = _build_dialog()
    dialog._on_skip()
    assert dialog.result == {"action": "skip"}

    dialog = _build_dialog()
    dialog._on_cancel()
    assert dialog.result == {"action": "skip"}


def test_on_open_explorer__missing_file(monkeypatch):
    dialog = _build_dialog()
    monkeypatch.setattr(batch_description_dialog.os.path, "exists", lambda _p: False)
    called = []
    monkeypatch.setattr(batch_description_dialog.messagebox, "showwarning", lambda *_a, **_k: called.append(True))

    dialog._on_open_explorer()
    assert called


def test_on_open_explorer__windows(monkeypatch):
    dialog = _build_dialog()
    monkeypatch.setattr(batch_description_dialog.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(batch_description_dialog.os, "name", "nt")
    called = []
    monkeypatch.setattr(batch_description_dialog.subprocess, "run", lambda cmd: called.append(cmd))

    dialog._on_open_explorer()
    assert called


def test_collect_batch_description__returns_result(monkeypatch):
    class DummyDialog:
        def __init__(self, *_args, **_kwargs):
            self.result = {"action": "save"}

    class DummyRoot:
        def mainloop(self):
            return None

    monkeypatch.setattr(batch_description_dialog.tk, "Tk", lambda: DummyRoot())
    monkeypatch.setattr(batch_description_dialog, "BatchDescriptionDialog", DummyDialog)

    result = batch_description_dialog.collect_batch_description("C:/file.jpg", 10)
    assert result == {"action": "save"}
