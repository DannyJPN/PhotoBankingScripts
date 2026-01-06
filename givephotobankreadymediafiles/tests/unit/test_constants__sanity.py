"""
Sanity tests for givephotobankreadymediafileslib/constants.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import constants


def test_get_status_column__suffix():
    assert constants.get_status_column("Adobe") == "Adobe status"


def test_get_category_column__suffix():
    assert constants.get_category_column("Shutter") == "Shutter kategorie"


def test_default_batch_limits__sane_ranges():
    assert constants.BATCH_SIZE_MIN < constants.BATCH_SIZE_MAX
    assert constants.DEFAULT_BATCH_SIZE >= constants.BATCH_SIZE_MIN
