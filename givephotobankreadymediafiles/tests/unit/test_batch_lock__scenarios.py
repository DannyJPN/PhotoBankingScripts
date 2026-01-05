"""
Unit tests for givephotobankreadymediafileslib/batch_lock.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import batch_lock


class DummyHandle:
    def __init__(self):
        self.closed = False

    def fileno(self):
        return 123

    def close(self):
        self.closed = True


def test_acquire_and_release__windows_locking(monkeypatch):
    handle = DummyHandle()
    calls = []

    def fake_open(_path, _mode):
        return handle

    def fake_locking(_fd, op, _size):
        calls.append(op)

    monkeypatch.setattr(batch_lock, "open_file_handle", fake_open)
    monkeypatch.setattr(batch_lock, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(batch_lock.os, "name", "nt")
    monkeypatch.setattr(batch_lock, "msvcrt", SimpleNamespace(LK_NBLCK=1, LK_UNLCK=2, locking=fake_locking))

    lock = batch_lock.BatchLock("C:/temp/batch.lock")
    lock.acquire()
    assert lock._locked is True
    assert calls == [1]

    lock.release()
    assert lock._locked is False
    assert handle.closed is True
    assert calls == [1, 2]


def test_acquire__double_acquire_raises(monkeypatch):
    handle = DummyHandle()
    monkeypatch.setattr(batch_lock, "open_file_handle", lambda _p, _m: handle)
    monkeypatch.setattr(batch_lock, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(batch_lock.os, "name", "nt")
    monkeypatch.setattr(batch_lock, "msvcrt", SimpleNamespace(LK_NBLCK=1, LK_UNLCK=2, locking=lambda *_: None))

    lock = batch_lock.BatchLock("C:/temp/batch.lock")
    lock.acquire()

    try:
        lock.acquire()
    except RuntimeError as exc:
        assert "already running" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for double acquire")


def test_acquire__lock_failure_releases_handle(monkeypatch):
    handle = DummyHandle()

    def fake_locking(_fd, _op, _size):
        raise OSError("busy")

    monkeypatch.setattr(batch_lock, "open_file_handle", lambda _p, _m: handle)
    monkeypatch.setattr(batch_lock, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(batch_lock.os, "name", "nt")
    monkeypatch.setattr(batch_lock, "msvcrt", SimpleNamespace(LK_NBLCK=1, LK_UNLCK=2, locking=fake_locking))

    lock = batch_lock.BatchLock("C:/temp/batch.lock")
    try:
        lock.acquire()
    except RuntimeError as exc:
        assert "lock unavailable" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError on lock failure")

    assert lock._locked is False
    assert lock._handle is None
    assert handle.closed is True


def test_context_manager__acquires_and_releases(monkeypatch):
    handle = DummyHandle()
    monkeypatch.setattr(batch_lock, "open_file_handle", lambda _p, _m: handle)
    monkeypatch.setattr(batch_lock, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(batch_lock.os, "name", "nt")
    monkeypatch.setattr(batch_lock, "msvcrt", SimpleNamespace(LK_NBLCK=1, LK_UNLCK=2, locking=lambda *_: None))

    lock = batch_lock.BatchLock("C:/temp/batch.lock")
    with lock as acquired:
        assert acquired is lock
        assert lock._locked is True

    assert lock._locked is False
