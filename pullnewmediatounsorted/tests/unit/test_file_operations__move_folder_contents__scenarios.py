"""
Unit tests for move_folder_contents in shared.file_operations.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "pullnewmediatounsorted"
sys.path.insert(0, str(package_root))

import shared.file_operations as file_operations


def test_move_folder_contents__moves_files_and_keeps_root(tmp_path):
    source = tmp_path / "source"
    nested = source / "nested"
    nested.mkdir(parents=True)
    target = tmp_path / "target"

    original = nested / "sample.txt"
    original.write_text("content", encoding="utf-8")

    file_operations.move_folder_contents(str(source), str(target))

    moved = target / "nested" / "sample.txt"
    assert source.exists()
    assert not original.exists()
    assert moved.exists()
    assert moved.read_text(encoding="utf-8") == "content"


def test_move_folder_contents__respects_pattern(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "target"

    screenshot = source / "Screenshot_1.png"
    regular = source / "photo.jpg"
    screenshot.write_text("screen", encoding="utf-8")
    regular.write_text("photo", encoding="utf-8")

    file_operations.move_folder_contents(str(source), str(target), pattern=r"Screenshot")

    assert (target / "Screenshot_1.png").exists()
    assert not screenshot.exists()
    assert regular.exists()
