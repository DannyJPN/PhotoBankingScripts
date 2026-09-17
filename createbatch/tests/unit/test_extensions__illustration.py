"""
Unit tests for illustration extensions list.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

from createbatchlib.illustration_extensions import ILLUSTRATION_EXTENSIONS


def test_illustration_extensions__expected_values():
    assert isinstance(ILLUSTRATION_EXTENSIONS, list)
    assert "ai" in ILLUSTRATION_EXTENSIONS
    assert "svg" in ILLUSTRATION_EXTENSIONS
