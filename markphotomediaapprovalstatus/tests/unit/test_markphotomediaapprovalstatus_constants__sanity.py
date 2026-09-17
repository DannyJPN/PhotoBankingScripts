"""
Unit tests for markphotomediaapprovalstatuslib/constants.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

from markphotomediaapprovalstatuslib import constants


def test_constants__types():
    assert isinstance(constants.DEFAULT_PHOTO_CSV_PATH, str)
    assert isinstance(constants.DEFAULT_LOG_DIR, str)
    assert isinstance(constants.STATUS_CHECKED, str)
