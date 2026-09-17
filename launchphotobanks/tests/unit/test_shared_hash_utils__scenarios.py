"""
Unit tests for launchphotobanks/shared/hash_utils.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "launchphotobanks"
sys.path.insert(0, str(package_root))

import shared.hash_utils as hash_utils


def test_compute_file_hash__md5(tmp_path):
    data_file = tmp_path / "data.bin"
    data_file.write_bytes(b"abc")

    result = hash_utils.compute_file_hash(str(data_file), method="md5")

    assert len(result) == 32
