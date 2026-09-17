"""
Security-focused tests for replacement guard logic.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

from removealreadysortedoutlib.removal_operations import should_replace_file


def test_should_replace_file_rejects_empty_source(tmp_path):
    source = tmp_path / "source.jpg"
    target = tmp_path / "target.jpg"
    source.write_bytes(b"")
    target.write_bytes(b"data")

    assert should_replace_file(str(source), str(target)) is False
