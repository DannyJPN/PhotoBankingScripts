"""
Unit tests for uploadtophotobanks/shared/csv_sanitizer.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

from shared.csv_sanitizer import sanitize_field, is_dangerous


def test_sanitize_field__dangerous_prefix():
    assert sanitize_field("=1+1") == "'=1+1"


def test_is_dangerous__safe_and_unsafe():
    assert is_dangerous("=1+1") is True
    assert is_dangerous("safe") is False
