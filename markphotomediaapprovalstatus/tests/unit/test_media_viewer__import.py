"""
Import smoke test for media_viewer module.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))


def test_import_media_viewer():
    import markphotomediaapprovalstatuslib.media_viewer  # noqa: F401
