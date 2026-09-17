"""
Import smoke tests for sortunsortedmedialib modules not yet covered.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))


def test_import_constants():
    import sortunsortedmedialib.constants  # noqa: F401


def test_import_matching_engine():
    import sortunsortedmedialib.matching_engine  # noqa: F401


def test_import_media_classifier():
    import sortunsortedmedialib.media_classifier  # noqa: F401


def test_import_media_helper():
    import sortunsortedmedialib.media_helper  # noqa: F401


def test_import_media_viewer():
    import sortunsortedmedialib.media_viewer  # noqa: F401


def test_import_path_builder():
    import sortunsortedmedialib.path_builder  # noqa: F401


def test_import_interactive():
    import sortunsortedmedialib.interactive  # noqa: F401
