"""
Unit tests for sortunsortedmedialib/path_builder.py.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

from sortunsortedmedialib import path_builder


def test_build_target_path():
    date = datetime(2024, 1, 2)
    path = path_builder.build_target_path("C:/base", "Foto", "jpg", "Cat", date, "Camera")
    assert "Foto" in path
    assert "2024" in path


def test_build_edited_target_path():
    date = datetime(2024, 1, 2)
    path = path_builder.build_edited_target_path("C:/base", "Foto", "jpg", "Cat", date, "Camera")
    assert "Upraven" in path


def test_ensure_unique_path(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("x", encoding="utf-8")
    unique = path_builder.ensure_unique_path(str(target))
    assert unique != str(target)
