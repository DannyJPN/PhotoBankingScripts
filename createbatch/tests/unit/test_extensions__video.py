"""
Unit tests for video extensions list.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

from createbatchlib.video_extensions import VIDEO_EXTENSIONS


def test_video_extensions__expected_values():
    assert isinstance(VIDEO_EXTENSIONS, list)
    for ext in ["mp4", "mov", "avi", "mkv", "webm"]:
        assert ext in VIDEO_EXTENSIONS
