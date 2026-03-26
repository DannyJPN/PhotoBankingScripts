"""
Unit tests for givephotobankreadymediafileslib/media_display.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import media_display


class DummyLabel:
    def __init__(self):
        self.configs = []
        self.width = 800
        self.height = 600

    def configure(self, **kwargs):
        self.configs.append(kwargs)

    def update_idletasks(self):
        return None

    def winfo_width(self):
        return self.width

    def winfo_height(self):
        return self.height


class DummyButton:
    def __init__(self):
        self.texts = []

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.texts.append(kwargs["text"])


class DummyScale:
    def __init__(self):
        self.values = []

    def set(self, value):
        self.values.append(value)


class DummyRoot:
    def __init__(self):
        self.after_calls = []

    def after(self, _ms, func):
        self.after_calls.append(func)
        return None


class DummyLock:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


class DummyCapture:
    def __init__(self, opened=True):
        self._opened = opened
        self.released = False
        self.set_calls = []

    def isOpened(self):
        return self._opened

    def get(self, _prop):
        if _prop == media_display.cv2.CAP_PROP_FPS:
            return 25
        if _prop == media_display.cv2.CAP_PROP_FRAME_COUNT:
            return 100
        return 0

    def read(self):
        return False, None

    def set(self, _prop, value):
        self.set_calls.append(( _prop, value))

    def release(self):
        self.released = True


def test_load_media__routes_to_video_or_image(monkeypatch):
    display = media_display.MediaDisplay(DummyRoot())
    called = []
    monkeypatch.setattr(media_display, "is_video_file", lambda _p: True)
    monkeypatch.setattr(display, "load_video", lambda _p: called.append("video"))
    monkeypatch.setattr(display, "load_image", lambda _p: called.append("image"))

    display.load_media("C:/file.mp4")
    assert called == ["video"]

    monkeypatch.setattr(media_display, "is_video_file", lambda _p: False)
    display.load_media("C:/file.jpg")
    assert called[-1] == "image"


def test_load_image__error_sets_label(monkeypatch):
    display = media_display.MediaDisplay(DummyRoot())
    display.media_label = DummyLabel()

    def raise_error(_p):
        raise OSError("boom")

    monkeypatch.setattr(media_display.Image, "open", raise_error)
    display.load_image("C:/file.jpg")
    assert any("Error loading image" in c.get("text", "") for c in display.media_label.configs)


def test_resize_image__no_state_returns():
    display = media_display.MediaDisplay(DummyRoot())
    display.resize_image()


def test_on_window_resize__schedules_resize(monkeypatch):
    root = DummyRoot()
    display = media_display.MediaDisplay(root)
    display.current_file_path = "C:/file.jpg"
    monkeypatch.setattr(media_display, "is_video_file", lambda _p: False)

    event = SimpleNamespace(widget=root)
    display.on_window_resize(event)
    assert root.after_calls


def test_load_video__open_failure(monkeypatch):
    display = media_display.MediaDisplay(DummyRoot())
    display.media_label = DummyLabel()
    display.video_lock = DummyLock()

    monkeypatch.setattr(media_display.cv2, "VideoCapture", lambda _p: DummyCapture(opened=False))
    display.load_video("C:/file.mp4")
    assert any("Error loading video" in c.get("text", "") for c in display.media_label.configs)


def test_toggle_video__delegates(monkeypatch):
    display = media_display.MediaDisplay(DummyRoot())
    called = []
    display.video_playing = True
    display.pause_video = lambda: called.append("pause")
    display.toggle_video()
    assert called == ["pause"]

    display.video_playing = False
    display.play_video = lambda: called.append("play")
    display.toggle_video()
    assert called[-1] == "play"


def test_pause_and_stop_video_updates_state():
    display = media_display.MediaDisplay(DummyRoot())
    display.play_button = DummyButton()
    display.video_progress = DummyScale()
    display.time_label = DummyLabel()
    display.video_lock = DummyLock()
    display.video_cap = DummyCapture(opened=True)

    display.pause_video()
    assert display.video_paused is True
    assert display.play_button.texts[-1] == "Play"

    display.stop_video()
    assert display.video_cap is None
    assert display.video_progress.values[-1] == 0


def test_seek_video__spawns_thread(monkeypatch):
    display = media_display.MediaDisplay(DummyRoot())
    display.current_file_path = "C:/file.mp4"
    display.video_cap = DummyCapture(opened=True)
    display.video_frame_count = 100
    display.video_lock = DummyLock()
    monkeypatch.setattr(media_display, "is_video_file", lambda _p: True)

    started = []

    class DummyThread:
        def __init__(self, target, args, daemon):
            started.append((target, args, daemon))

        def start(self):
            return None

    monkeypatch.setattr(media_display.threading, "Thread", DummyThread)
    display.seek_video("50")
    assert started


def test_update_time_display__updates_progress():
    display = media_display.MediaDisplay(DummyRoot())
    display.time_label = DummyLabel()
    display.video_progress = DummyScale()
    display.video_cap = object()
    display.video_fps = 25
    display.video_frame_count = 100
    display.video_duration = 4
    display.current_frame_number = 50

    display._update_time_display()
    assert display.video_progress.values[-1] == 50.0
