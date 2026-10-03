"""
Security-focused tests for duplicate-removal guard logic.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

from removealreadysortedoutlib.removal_operations import handle_duplicate


def test_removal_operations__handle_duplicate__keeps_source_when_no_target_exists(tmp_path):
    """
    A stale or incorrect hash-map entry pointing at a target path that no longer
    exists must never cause the source file to be deleted.
    """
    source = tmp_path / "source.jpg"
    source.write_bytes(b"data")
    missing_target = tmp_path / "missing_target.jpg"

    handle_duplicate(str(source), [str(missing_target)])

    assert source.exists()
