"""
Performance-oriented tests for copy_files_with_preserved_dates.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "integratesortedphotos"
sys.path.insert(0, str(package_root))

from integratesortedphotoslib.copy_files import copy_files_with_preserved_dates


def test_copy_files_bulk(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()

    for i in range(50):
        (src / f"file_{i}.txt").write_text(f"data {i}", encoding="utf-8")

    copy_files_with_preserved_dates(str(src), str(dest))
    assert (dest / "file_49.txt").exists()
