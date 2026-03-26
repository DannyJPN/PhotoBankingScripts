"""
Import smoke test for integrate_sorted_photos.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "integratesortedphotos"
sys.path.insert(0, str(package_root))


def test_import_integrate_sorted_photos():
    import integrate_sorted_photos  # noqa: F401
