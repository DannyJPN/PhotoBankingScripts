"""
Import smoke test for sortunsortedmediafile.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))


def test_import_sortunsortedmediafile():
    import sortunsortedmediafile  # noqa: F401
