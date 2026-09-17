"""
Unit tests for launchphotobankslib/constants.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "launchphotobanks"
sys.path.insert(0, str(package_root))

from launchphotobankslib import constants


def test_constants__types():
    assert isinstance(constants.DEFAULT_BANK_CSV, str)
    assert isinstance(constants.DEFAULT_LOG_DIR, str)
    assert isinstance(constants.COLUMN_BANK_NAME, str)
    assert isinstance(constants.COLUMN_URL, str)
