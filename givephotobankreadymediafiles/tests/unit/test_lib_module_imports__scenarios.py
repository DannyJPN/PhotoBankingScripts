"""
Import smoke tests for givephotobankreadymediafileslib modules.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))


def test_import_ai_coordinator():
    import givephotobankreadymediafileslib.ai_coordinator  # noqa: F401


def test_import_alternative_generator():
    import givephotobankreadymediafileslib.alternative_generator  # noqa: F401


def test_import_batch_description_dialog():
    import givephotobankreadymediafileslib.batch_description_dialog  # noqa: F401


def test_import_batch_lock():
    import givephotobankreadymediafileslib.batch_lock  # noqa: F401


def test_import_batch_manager():
    import givephotobankreadymediafileslib.batch_manager  # noqa: F401


def test_import_batch_prompts():
    import givephotobankreadymediafileslib.batch_prompts  # noqa: F401


def test_import_batch_state():
    import givephotobankreadymediafileslib.batch_state  # noqa: F401


def test_import_categories_manager():
    import givephotobankreadymediafileslib.categories_manager  # noqa: F401


def test_import_constants():
    import givephotobankreadymediafileslib.constants  # noqa: F401


def test_import_editorial_dialog():
    import givephotobankreadymediafileslib.editorial_dialog  # noqa: F401


def test_import_media_display():
    import givephotobankreadymediafileslib.media_display  # noqa: F401


def test_import_media_helper():
    import givephotobankreadymediafileslib.media_helper  # noqa: F401


def test_import_media_processor():
    import givephotobankreadymediafileslib.media_processor  # noqa: F401


def test_import_media_viewer_refactored():
    import givephotobankreadymediafileslib.media_viewer_refactored  # noqa: F401


def test_import_media_viewer():
    import givephotobankreadymediafileslib.media_viewer  # noqa: F401


def test_import_mediainfo_loader():
    import givephotobankreadymediafileslib.mediainfo_loader  # noqa: F401


def test_import_metadata_generator():
    import givephotobankreadymediafileslib.metadata_generator  # noqa: F401


def test_import_metadata_validator():
    import givephotobankreadymediafileslib.metadata_validator  # noqa: F401


def test_import_tag_entry():
    import givephotobankreadymediafileslib.tag_entry  # noqa: F401


def test_import_ui_components():
    import givephotobankreadymediafileslib.ui_components  # noqa: F401


def test_import_viewer_state():
    import givephotobankreadymediafileslib.viewer_state  # noqa: F401
