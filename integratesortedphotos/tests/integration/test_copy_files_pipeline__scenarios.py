"""
Integration tests for integratesortedphotos copy pipeline.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "integratesortedphotos"
sys.path.insert(0, str(package_root))

from integratesortedphotoslib.copy_files import copy_files_with_preserved_dates


def test_copy_files_with_preserved_dates_copies_tree(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    (src / "nested").mkdir(parents=True)
    file_path = src / "nested" / "photo.jpg"
    file_path.write_bytes(b"data")

    copy_files_with_preserved_dates(str(src), str(dest))

    copied = dest / "nested" / "photo.jpg"
    assert copied.exists()
