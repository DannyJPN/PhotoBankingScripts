"""
Unit tests for sortunsortedmedialib/interactive.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

from sortunsortedmedialib import interactive


def test_ask_for_category_returns_default():
    assert interactive.ask_for_category("C:/file.jpg") == "Ostatn¡"
