"""
Unit tests for removealreadysortedoutlib/constants.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

from removealreadysortedoutlib import constants


def test_constants__types():
    assert isinstance(constants.DEFAULT_UNSORTED_FOLDER, str)
    assert isinstance(constants.DEFAULT_TARGET_FOLDER, str)
    assert isinstance(constants.DEFAULT_LOG_DIR, str)
