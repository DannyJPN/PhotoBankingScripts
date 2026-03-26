"""
Unit tests for integratesortedphotos/integrate_sorted_photos.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "integratesortedphotos"
sys.path.insert(0, str(package_root))

import integrate_sorted_photos as main_module


def test_main__missing_sorted_folder(monkeypatch):
    args = SimpleNamespace(sortedFolder="C:/missing", targetFolder="C:/target", log_dir="C:/logs", debug=False)
    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(main_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(main_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(main_module.os.path, "exists", lambda _p: False)

    assert main_module.main() is None


def test_main__calls_copy(monkeypatch):
    args = SimpleNamespace(sortedFolder="C:/sorted", targetFolder="C:/target", log_dir="C:/logs", debug=False)
    monkeypatch.setattr(main_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(main_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(main_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(main_module.os.path, "exists", lambda _p: True)
    called = []
    monkeypatch.setattr(main_module, "copy_files_with_preserved_dates", lambda *_a: called.append(True))

    main_module.main()
    assert called
