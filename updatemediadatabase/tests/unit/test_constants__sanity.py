"""
Sanity tests for updatemedialdatabaselib/constants.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))

from updatemedialdatabaselib import constants


def test_default_paths_present():
    assert constants.DEFAULT_MEDIA_CSV_PATH
    assert constants.DEFAULT_LIMITS_CSV_PATH


def test_numbering_limits():
    assert constants.MIN_NUMBER_WIDTH <= constants.DEFAULT_NUMBER_WIDTH <= constants.MAX_NUMBER_WIDTH
    assert constants.MAX_NUMBER == 999999
