"""
Import smoke test for uploadtophotobanks.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))


def test_import_uploadtophotobanks():
    import uploadtophotobanks  # noqa: F401
