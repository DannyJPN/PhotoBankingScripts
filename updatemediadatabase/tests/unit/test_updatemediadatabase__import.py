"""
Import smoke test for updatemediadatabase.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))


def test_import_updatemediadatabase():
    import updatemediadatabase  # noqa: F401
