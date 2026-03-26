"""
Performance-oriented tests for duplicate detection.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

from removealreadysortedoutlib.removal_operations import find_duplicates


def test_find_duplicates_bulk():
    unsorted_files = [f"C:/unsorted/file_{i}.jpg" for i in range(500)]
    target_map = {f"file_{i}.jpg": [f"C:/target/file_{i}.jpg"] for i in range(0, 500, 2)}
    duplicates = find_duplicates(unsorted_files, target_map)
    assert len(duplicates) == 250
