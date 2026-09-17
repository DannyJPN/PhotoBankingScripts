"""
Performance-oriented tests for file type splitting.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))

from updatemediadatabase import split_files_by_type


def test_split_files_by_type_bulk():
    files = [f"C:/media/file_{i}.jpg" for i in range(300)]
    files += [f"C:/media/clip_{i}.mp4" for i in range(100)]
    result = split_files_by_type(files)
    assert len(result["jpg"]) == 300
    assert len(result["videos"]) == 100
