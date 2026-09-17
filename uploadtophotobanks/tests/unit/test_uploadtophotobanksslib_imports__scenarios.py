"""
Import smoke tests for uploadtophotobanksslib modules.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))


def test_import_connection_manager():
    import uploadtophotobanksslib.connection_manager  # noqa: F401


def test_import_constants():
    import uploadtophotobanksslib.constants  # noqa: F401


def test_import_credentials_manager():
    import uploadtophotobanksslib.credentials_manager  # noqa: F401


def test_import_file_validator():
    import uploadtophotobanksslib.file_validator  # noqa: F401


def test_import_uploader():
    import uploadtophotobanksslib.uploader  # noqa: F401
