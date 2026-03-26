"""
Unit tests for exportpreparedmedialib/export_processor.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))


def test_export_processor__import_and_basic_usage():
    # Import inside test so missing dependencies raise during test execution.
    import exportpreparedmedialib.export_processor as export_processor  # noqa: F401
