"""
Import smoke test for shared.exif_handler.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "pullnewmediatounsorted"
sys.path.insert(0, str(package_root))


def test_import_exif_handler():
    import shared.exif_handler  # noqa: F401
