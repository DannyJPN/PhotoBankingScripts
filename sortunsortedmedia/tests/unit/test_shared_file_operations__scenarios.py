"""
Unit tests for sortunsortedmedia/shared/file_operations.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

import shared.file_operations as file_operations


def test_list_files__non_recursive(tmp_path):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.log").write_text("b", encoding="utf-8")

    files = file_operations.list_files(str(tmp_path), pattern="\\.txt$", recursive=False)
    assert any(path.endswith("a.txt") for path in files)
    assert all("b.log" not in path for path in files)


def test_ensure_directory__creates(tmp_path):
    target = tmp_path / "nested"
    file_operations.ensure_directory(str(target))
    assert target.exists()


def test_save_csv__writes_rows(tmp_path):
    target = tmp_path / "report.csv"

    file_operations.save_csv(
        [{"category": "jpg_files", "file_path": "C:/photo.jpg"}],
        str(target),
        ["category", "file_path"],
    )

    content = target.read_text(encoding="utf-8-sig")
    assert "category,file_path" in content
    assert "jpg_files" in content


def test_save_json__writes_json(tmp_path):
    target = tmp_path / "report.json"

    file_operations.save_json({"records": [{"category": "jpg_files"}]}, str(target))

    content = target.read_text(encoding="utf-8")
    assert '"records"' in content
    assert '"jpg_files"' in content
