"""
Unit tests for markmediaascheckedlib/constants.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

from markmediaascheckedlib import constants


def test_constants__types():
    assert isinstance(constants.DEFAULT_PHOTO_CSV_FILE, str)
    assert isinstance(constants.STATUS_READY, str)
    assert isinstance(constants.STATUS_CHECKED, str)
