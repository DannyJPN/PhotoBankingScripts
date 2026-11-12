"""
Performance-oriented tests for duplicate detection.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

from shared.hash_utils import compute_file_hash
from removealreadysortedoutlib.removal_operations import find_duplicates


def test_find_duplicates_bulk(tmp_path):
    unsorted_dir = tmp_path / "unsorted"
    target_dir = tmp_path / "target"
    unsorted_dir.mkdir()
    target_dir.mkdir()

    unsorted_files = []
    target_map = {}
    for i in range(500):
        content = f"content {i % 2}".encode()
        source = unsorted_dir / f"file_{i}.jpg"
        source.write_bytes(content)
        unsorted_files.append(str(source))
        if i % 2 == 0:
            target = target_dir / f"file_{i}.jpg"
            target.write_bytes(content)
            target_map.setdefault(compute_file_hash(str(target)), []).append(str(target))

    duplicates = find_duplicates(unsorted_files, target_map)

    assert len(duplicates) == 250
