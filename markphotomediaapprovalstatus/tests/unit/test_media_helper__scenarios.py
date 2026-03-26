"""
Unit tests for markphotomediaapprovalstatuslib/media_helper.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

from markphotomediaapprovalstatuslib.media_helper import (
    is_video_file,
    is_jpg_file,
    is_media_file,
)


def test_is_video_file():
    assert is_video_file("video.mp4") is True
    assert is_video_file("image.jpg") is False


def test_is_jpg_file():
    assert is_jpg_file("photo.jpg") is True
    assert is_jpg_file("photo.png") is False


def test_is_media_file():
    assert is_media_file("photo.jpg") is True
    assert is_media_file("clip.mp4") is True
    assert is_media_file("doc.txt") is False
