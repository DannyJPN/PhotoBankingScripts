"""
Unit tests for givephotobankreadymediafiles/shared/exif_handler.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

import shared.exif_handler as exif_handler


def test_update_exif_metadata__raises_when_missing(monkeypatch):
    monkeypatch.setattr(exif_handler.shutil, "which", lambda _n: None)
    monkeypatch.setattr(exif_handler.os.path, "isdir", lambda _p: False)
    monkeypatch.setattr(exif_handler.os.path, "isfile", lambda _p: False)
    monkeypatch.setattr(exif_handler.os, "access", lambda _p, _m: False)

    with pytest.raises(RuntimeError):
        exif_handler.update_exif_metadata("C:/media/file.jpg", {}, tool_path=None)
