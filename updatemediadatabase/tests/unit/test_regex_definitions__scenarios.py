"""
Unit tests for updatemedialdatabaselib/regex_definitions.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "updatemediadatabase"
sys.path.insert(0, str(package_root))

from updatemedialdatabaselib import regex_definitions


def test_any_edit_pattern_matches():
    assert regex_definitions.ANY_EDIT_PATTERN.search("file_bw.jpg") is not None


def test_original_filename_pattern():
    match = regex_definitions.ORIGINAL_FILENAME_PATTERN.match("IMG_0001_bw.jpg")
    assert match is not None
