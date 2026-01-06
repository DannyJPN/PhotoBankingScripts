"""
Import smoke tests for updatemedialdatabaselib modules.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))


def test_import_constants():
    import updatemedialdatabaselib.constants  # noqa: F401


def test_import_edit_utils():
    import updatemedialdatabaselib.edit_utils  # noqa: F401


def test_import_exif_downloader():
    import updatemedialdatabaselib.exif_downloader  # noqa: F401


def test_import_exif_handler():
    import updatemedialdatabaselib.exif_handler  # noqa: F401


def test_import_media_processor():
    import updatemedialdatabaselib.media_processor  # noqa: F401


def test_import_photo_analyzer():
    import updatemedialdatabaselib.photo_analyzer  # noqa: F401


def test_import_regex_definitions():
    import updatemedialdatabaselib.regex_definitions  # noqa: F401
