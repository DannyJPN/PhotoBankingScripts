"""
Unit tests for givephotobankreadymediafiles/preparemediafile.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

import preparemediafile as script


def test_main__missing_file(monkeypatch):
    args = SimpleNamespace(
        file="C:/missing.jpg",
        media_csv="media.csv",
        categories_csv="cats.csv",
        log_dir="logs",
        debug=False,
    )

    monkeypatch.setattr(script, "parse_arguments", lambda: args)
    monkeypatch.setattr(script, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(script, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(script.os.path, "exists", lambda _p: False)

    assert script.main() == 1


def test_main__no_metadata_saved(monkeypatch):
    args = SimpleNamespace(
        file="C:/file.jpg",
        media_csv="media.csv",
        categories_csv="cats.csv",
        log_dir="logs",
        debug=False,
    )

    monkeypatch.setattr(script, "parse_arguments", lambda: args)
    monkeypatch.setattr(script, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(script, "setup_logging", lambda **_k: None)

    def fake_exists(path):
        return path == args.file

    monkeypatch.setattr(script.os.path, "exists", fake_exists)
    monkeypatch.setattr(script, "load_categories", lambda _p: {})
    monkeypatch.setattr(script, "load_media_records", lambda _p: [])
    monkeypatch.setattr(script, "show_media_viewer", lambda *_a, **_k: None)

    assert script.main() == 0
