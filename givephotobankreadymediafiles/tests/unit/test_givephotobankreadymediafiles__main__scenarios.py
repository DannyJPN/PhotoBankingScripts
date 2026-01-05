"""
Unit tests for givephotobankreadymediafiles/givephotobankreadymediafiles.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

import givephotobankreadymediafiles as main_module


def test_main__check_batch_status(monkeypatch):
    args = SimpleNamespace(
        media_csv="media.csv",
        categories_csv="cats.csv",
        log_dir="logs",
        debug=False,
        max_count=1,
        interval=0,
        batch_mode=False,
        batch_size=1,
        batch_wait_timeout=0,
        batch_poll_interval=0,
        check_batch_status=True,
    )

    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(main_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(main_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(main_module, "get_config", lambda: object())
    monkeypatch.setattr(main_module, "check_batch_statuses", lambda: ["ok"])

    assert main_module.main() == 0


def test_main__batch_mode_lock_failure(monkeypatch):
    args = SimpleNamespace(
        media_csv="media.csv",
        categories_csv="cats.csv",
        log_dir="logs",
        debug=False,
        max_count=1,
        interval=0,
        batch_mode=True,
        batch_size=1,
        batch_wait_timeout=0,
        batch_poll_interval=0,
        check_batch_status=False,
    )

    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(main_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(main_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(main_module, "get_config", lambda: object())

    class DummyLock:
        def __init__(self, _p):
            return None

        def acquire(self):
            raise RuntimeError("locked")

    monkeypatch.setattr(main_module, "BatchLock", DummyLock)
    assert main_module.main() == 1


def test_main__no_media_records(monkeypatch):
    args = SimpleNamespace(
        media_csv="media.csv",
        categories_csv="cats.csv",
        log_dir="logs",
        debug=False,
        max_count=1,
        interval=0,
        batch_mode=False,
        batch_size=1,
        batch_wait_timeout=0,
        batch_poll_interval=0,
        check_batch_status=False,
    )

    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(main_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(main_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(main_module, "get_config", lambda: object())
    monkeypatch.setattr(main_module, "load_media_records", lambda _p: [])

    assert main_module.main() == 1


def test_main__no_unprocessed(monkeypatch):
    args = SimpleNamespace(
        media_csv="media.csv",
        categories_csv="cats.csv",
        log_dir="logs",
        debug=False,
        max_count=1,
        interval=0,
        batch_mode=False,
        batch_size=1,
        batch_wait_timeout=0,
        batch_poll_interval=0,
        check_batch_status=False,
    )

    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(main_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(main_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(main_module, "get_config", lambda: object())
    monkeypatch.setattr(main_module, "load_media_records", lambda _p: [{"Cesta": "C:/file.jpg"}])
    monkeypatch.setattr(main_module, "load_categories", lambda _p: {})
    monkeypatch.setattr(main_module, "find_unprocessed_records", lambda _r: [])
    monkeypatch.setattr(main_module, "read_json", lambda *_a, **_k: {})

    assert main_module.main() == 0


def test_main__process_records(monkeypatch):
    args = SimpleNamespace(
        media_csv="media.csv",
        categories_csv="cats.csv",
        log_dir="logs",
        debug=False,
        max_count=1,
        interval=0,
        batch_mode=False,
        batch_size=1,
        batch_wait_timeout=0,
        batch_poll_interval=0,
        check_batch_status=False,
    )

    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(main_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(main_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(main_module, "get_config", lambda: object())
    monkeypatch.setattr(main_module, "load_media_records", lambda _p: [{"Cesta": "C:/file.jpg"}])
    monkeypatch.setattr(main_module, "load_categories", lambda _p: {})
    monkeypatch.setattr(main_module, "find_unprocessed_records", lambda _r: [{"Cesta": "C:/file.jpg"}])
    monkeypatch.setattr(main_module, "read_json", lambda *_a, **_k: {})
    monkeypatch.setattr(main_module, "process_unmatched_files", lambda *_a, **_k: {"processed": 1, "failed": 0, "skipped": 0})

    assert main_module.main() == 0
