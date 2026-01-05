"""
Unit tests for updatemedialdatabaselib/edit_utils.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))

from updatemedialdatabaselib import edit_utils


def test_get_edit_type():
    assert edit_utils.get_edit_type("IMG_0001_bw.jpg") == "bw"
    assert edit_utils.get_edit_type("IMG_0001.jpg") is None


def test_is_edited_file():
    assert edit_utils.is_edited_file("IMG_0001_bw.jpg") is True
    assert edit_utils.is_edited_file("IMG_0001.jpg") is False


def test_get_original_filename():
    assert edit_utils.get_original_filename("IMG_0001_bw.jpg") == "IMG_0001.jpg"


def test_modify_description_for_edit():
    result = edit_utils.modify_description_for_edit("Forest", "bw")
    assert result.startswith("Black and white image")


def test_modify_keywords_for_edit():
    result = edit_utils.modify_keywords_for_edit("forest", "bw")
    assert "black and white" in result


def test_update_metadata_for_edit():
    updated = edit_utils.update_metadata_for_edit({"Description": "Desc", "Keywords": "one"}, "bw")
    assert "EditType" in updated
