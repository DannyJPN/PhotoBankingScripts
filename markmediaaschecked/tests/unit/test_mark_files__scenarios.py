"""
Unit tests for markmediaascheckedlib/mark_files.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markmediaaschecked"
sys.path.insert(0, str(package_root))

from markmediaascheckedlib import constants
from markmediaascheckedlib.mark_files import mark_files_as_checked


def test_mark_files_as_checked__replaces_status():
    data = [{"Status": constants.STATUS_READY}]
    result = mark_files_as_checked(data)
    assert result[0]["Status"] == constants.STATUS_CHECKED
