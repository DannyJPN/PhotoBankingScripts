"""
Import smoke tests for top-level scripts.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))


def test_import_givephotobankreadymediafiles():
    import givephotobankreadymediafiles  # noqa: F401


def test_import_generatealternatives():
    import generatealternatives  # noqa: F401


def test_import_preparemediafile():
    import preparemediafile  # noqa: F401
