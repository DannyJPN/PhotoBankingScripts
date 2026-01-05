"""
Unit tests for uploadtophotobanks/uploadtophotobanks.py helpers.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

import uploadtophotobanks as main_module


def test_get_selected_photobanks__all(monkeypatch):
    args = SimpleNamespace(
        all=True, shutterstock=False, pond5=False, rf123=False, depositphotos=False,
        alamy=False, dreamstime=False, adobestock=False, canstockphoto=False
    )

    class DummyCreds:
        def list_photobanks(self):
            return ["ShutterStock", "Pond5"]

    selected = main_module.get_selected_photobanks(args, DummyCreds())
    assert selected == ["ShutterStock", "Pond5"]


def test_validate_input_files(monkeypatch):
    args = SimpleNamespace(media_folder="C:/media", export_dir="C:/export")
    monkeypatch.setattr(main_module.os.path, "exists", lambda _p: False)
    assert main_module.validate_input_files(args) is False
