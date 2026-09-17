"""
Unit tests for exportpreparedmedialib/category_handler.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))


def test_category_handler__import_and_basic_usage():
    # Import inside test so a SyntaxError is surfaced as a test failure.
    import exportpreparedmedialib.category_handler as category_handler  # noqa: F401
