"""
Unit tests for exportpreparedmedia/shared/csv_handler.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))


def test_csv_handler__import_and_basic_usage():
    # Import inside test so missing dependencies raise during test execution.
    import shared.csv_handler as csv_handler  # noqa: F401
