"""
Sanity tests for uploadtophotobanksslib/constants.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

from uploadtophotobanksslib import constants


def test_get_status_column():
    assert constants.get_status_column("Bank") == "Bank status"


def test_get_category_column():
    assert constants.get_category_column("Bank") == "Bank kategorie"
