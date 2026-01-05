"""
Sanity tests for sortunsortedmedialib/constants.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

from sortunsortedmedialib import constants


def test_default_paths_present():
    assert constants.DEFAULT_UNSORTED_FOLDER
    assert constants.DEFAULT_TARGET_FOLDER


def test_extension_types_contains_jpg():
    assert constants.EXTENSION_TYPES["jpg"] == "Foto"
