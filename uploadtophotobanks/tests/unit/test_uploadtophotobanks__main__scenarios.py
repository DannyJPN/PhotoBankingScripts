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


def test_parse_arguments__resume_flags(monkeypatch, tmp_path):
    resume_log = tmp_path / "upload.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "uploadtophotobanks.py",
            "--resume",
            "--resume-log",
            str(resume_log),
        ],
    )

    args = main_module.parse_arguments()

    assert args.resume is True
    assert args.resume_log == str(resume_log)


def test_load_resume_failed_files__groups_failures(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "load_csv",
        lambda _path: [
            {"photobank": "ShutterStock", "filename": "a.jpg", "status": "failure"},
            {"photobank": "ShutterStock", "filename": "b.jpg", "status": "success"},
            {"photobank": "Pond5", "filename": "c.jpg", "status": "error"},
        ],
    )

    failed = main_module._load_resume_failed_files("C:/log.csv", "C:/logs")

    assert failed == {"ShutterStock": {"a.jpg"}, "Pond5": {"c.jpg"}}
