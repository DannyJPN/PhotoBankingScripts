"""
Unit tests for integratesortedphotoslib/constants.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "integratesortedphotos"
sys.path.insert(0, str(package_root))

from integratesortedphotoslib import constants


def test_constants__types():
    assert isinstance(constants.SOURCE_DIR, str)
    assert isinstance(constants.DEST_DIR, str)
