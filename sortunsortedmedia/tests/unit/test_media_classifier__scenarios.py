"""
Unit tests for sortunsortedmedialib/media_classifier.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

import sortunsortedmedialib.media_classifier as media_classifier


def test_detect_camera_from_filename():
    assert media_classifier.detect_camera_from_filename("DSC00001") == "Sony CyberShot W810"


def test_classify_media_file(monkeypatch):
    monkeypatch.setattr(media_classifier, "is_edited_file", lambda _f: False)
    monkeypatch.setattr(media_classifier, "combine_regex_and_exif_detection", lambda _p, _c: "Camera")
    media_type, camera, is_edited, edit_type = media_classifier.classify_media_file("C:/file.jpg")
    assert camera == "Camera"
    assert is_edited is False
