"""
Performance-oriented tests for camera detection.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

from sortunsortedmedialib.media_classifier import detect_camera_from_filename


def test_detect_camera_from_filename_bulk():
    filenames = [f"DSC_{i:04d}" for i in range(500)]
    results = [detect_camera_from_filename(name) for name in filenames]
    assert len(results) == 500
