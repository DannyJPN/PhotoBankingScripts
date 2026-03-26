"""
Unit tests for givephotobankreadymediafileslib/media_viewer_refactored.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import media_viewer_refactored


class DummyRoot:
    def __init__(self):
        self.destroyed = False

    def destroy(self):
        self.destroyed = True


class DummyLabel:
    def __init__(self):
        self.text = None

    def configure(self, **kwargs):
        self.text = kwargs.get("text")


class DummyEntry:
    def __init__(self):
        self.focused = False

    def focus(self):
        self.focused = True


def _build_viewer():
    viewer = media_viewer_refactored.MediaViewerRefactored.__new__(media_viewer_refactored.MediaViewerRefactored)
    viewer.root = DummyRoot()
    viewer.viewer_state = SimpleNamespace(
        current_file_path=None,
        current_record=None,
        completion_callback=None,
        collect_metadata=lambda: {"title": "t", "description": "d", "keywords": "k", "editorial": False},
        load_metadata_from_record=lambda _r: None,
        title_entry=DummyEntry(),
    )
    viewer.media_display = SimpleNamespace(clear_media=lambda: None, load_media=lambda _p: None)
    viewer.categories_manager = SimpleNamespace(
        load_existing_categories=lambda _r: None,
        collect_selected_categories=lambda: {"ShutterStock": ["A"]},
    )
    viewer.ui_components = SimpleNamespace(file_path_label=DummyLabel(), model_combo=SimpleNamespace(get=lambda: "Model A"))
    viewer.metadata_validator = SimpleNamespace(update_all_button_states=lambda: None)
    return viewer


def test_on_model_selected__updates_buttons():
    viewer = _build_viewer()
    called = []
    viewer.metadata_validator.update_all_button_states = lambda: called.append(True)

    viewer.on_model_selected()
    assert called


def test_load_media__wires_state():
    viewer = _build_viewer()
    called = []
    viewer.media_display.clear_media = lambda: called.append("clear")
    viewer.media_display.load_media = lambda _p: called.append("load")
    viewer.viewer_state.load_metadata_from_record = lambda _r: called.append("metadata")
    viewer.categories_manager.load_existing_categories = lambda _r: called.append("categories")
    viewer.metadata_validator.update_all_button_states = lambda: called.append("buttons")

    viewer.load_media("C:/file.jpg", {"a": 1}, completion_callback=lambda _m: True)
    assert viewer.viewer_state.current_file_path == "C:/file.jpg"
    assert viewer.ui_components.file_path_label.text == "C:/file.jpg"
    assert "load" in called
    assert viewer.viewer_state.title_entry.focused is True


def test_save_metadata__no_record(monkeypatch):
    viewer = _build_viewer()
    viewer.viewer_state.current_record = None
    called = []
    monkeypatch.setattr(media_viewer_refactored.messagebox, "showwarning", lambda *_a, **_k: called.append(True))

    viewer.save_metadata()
    assert called


def test_save_metadata__success():
    viewer = _build_viewer()
    viewer.viewer_state.current_record = {"a": 1}
    viewer.viewer_state.completion_callback = lambda _m: True

    viewer.save_metadata()
    assert viewer.root.destroyed is True


def test_save_metadata__failure(monkeypatch):
    viewer = _build_viewer()
    viewer.viewer_state.current_record = {"a": 1}
    viewer.viewer_state.completion_callback = lambda _m: False
    called = []
    monkeypatch.setattr(media_viewer_refactored.messagebox, "showerror", lambda *_a, **_k: called.append(True))

    viewer.save_metadata()
    assert called
    assert viewer.root.destroyed is False


def test_reject_metadata__no_record(monkeypatch):
    viewer = _build_viewer()
    viewer.viewer_state.current_record = None
    called = []
    monkeypatch.setattr(media_viewer_refactored.messagebox, "showwarning", lambda *_a, **_k: called.append(True))

    viewer.reject_metadata()
    assert called


def test_reject_metadata__confirmed(monkeypatch):
    viewer = _build_viewer()
    viewer.viewer_state.current_record = {"a": 1}
    viewer.viewer_state.current_file_path = "C:/file.jpg"
    called = []
    viewer.viewer_state.completion_callback = lambda _m: called.append(_m)
    monkeypatch.setattr(media_viewer_refactored.messagebox, "askyesno", lambda *_a, **_k: True)

    viewer.reject_metadata()
    assert called
    assert viewer.root.destroyed is True


def test_open_in_explorer__no_file(monkeypatch):
    viewer = _build_viewer()
    viewer.viewer_state.current_file_path = None
    called = []
    monkeypatch.setattr(media_viewer_refactored.messagebox, "showwarning", lambda *_a, **_k: called.append(True))

    viewer.open_in_explorer()
    assert called


def test_open_in_explorer__windows(monkeypatch):
    viewer = _build_viewer()
    viewer.viewer_state.current_file_path = "C:/file.jpg"
    monkeypatch.setattr(media_viewer_refactored.platform, "system", lambda: "Windows")
    called = []
    monkeypatch.setattr(media_viewer_refactored.subprocess, "run", lambda *_a, **_k: SimpleNamespace(returncode=0))
    viewer.open_in_explorer()
    assert viewer.root.destroyed is False


def test_on_window_close__exits(monkeypatch):
    viewer = _build_viewer()
    called = []
    monkeypatch.setattr(media_viewer_refactored.sys, "exit", lambda code: called.append(code))

    viewer.on_window_close()
    assert viewer.root.destroyed is True
    assert called == [0]


def test_show_media_viewer__creates_and_loads(monkeypatch):
    called = []

    class DummyRoot:
        def update_idletasks(self):
            return None

        def winfo_screenwidth(self):
            return 1000

        def winfo_screenheight(self):
            return 800

        def winfo_width(self):
            return 500

        def winfo_height(self):
            return 400

        def geometry(self, _value):
            called.append("geometry")

        def mainloop(self):
            called.append("mainloop")

    class DummyViewer:
        def __init__(self, root, _target, _categories):
            self.root = root

        def load_media(self, file_path, record, completion_callback):
            called.append((file_path, record, completion_callback))

    monkeypatch.setattr(media_viewer_refactored.tk, "Tk", lambda: DummyRoot())
    monkeypatch.setattr(media_viewer_refactored, "MediaViewerRefactored", DummyViewer)

    media_viewer_refactored.show_media_viewer("C:/file.jpg", {"a": 1}, None, {})
    assert ("C:/file.jpg", {"a": 1}, None) in called
