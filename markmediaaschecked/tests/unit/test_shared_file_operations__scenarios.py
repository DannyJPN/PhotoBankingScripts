"""
Unit tests for markmediaaschecked/shared/file_operations.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

import shared.file_operations as file_ops


def test_copy_file__creates_dest_dir(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("x", encoding="utf-8")
    dest = tmp_path / "out" / "dest.txt"

    file_ops.copy_file(str(src), str(dest), overwrite=True)

    assert dest.exists()
