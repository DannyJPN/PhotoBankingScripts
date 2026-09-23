"""
Unit tests for pullnewmediatounsorted/shared/file_operations.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "pullnewmediatounsorted"
sys.path.insert(0, str(package_root))

import shared.file_operations as file_operations


def test_save_csv__writes_rows(tmp_path):
    target = tmp_path / "report.csv"

    file_operations.save_csv(
        [{"category": "media", "file_path": "C:/file.jpg"}],
        str(target),
        ["category", "file_path"],
    )

    content = target.read_text(encoding="utf-8-sig")
    assert "category,file_path" in content
    assert "media" in content


def test_save_json__writes_json(tmp_path):
    target = tmp_path / "report.json"

    file_operations.save_json({"records": [{"category": "media"}]}, str(target))

    content = target.read_text(encoding="utf-8")
    assert '"records"' in content
    assert '"media"' in content
