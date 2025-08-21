"""
Test-specific constants for RemoveAlreadySortedOut module.

This module provides test-only values as required by CLAUDE.md global rules.
"""

from typing import Dict, List

# Test directories - safe paths for testing
TEST_UNSORTED_FOLDER: str = "F:/Dropbox/Scripts/Python/Fotobanking/removealreadysortedout/tests/data/unsorted"
TEST_TARGET_FOLDER: str = "F:/Dropbox/Scripts/Python/Fotobanking/removealreadysortedout/tests/data/sorted"
TEST_LOG_DIR: str = "F:/Dropbox/Scripts/Python/Fotobanking/removealreadysortedout/tests/logs"

# Test-only configuration
TEST_LOG_LEVEL: str = "DEBUG"

# Test file patterns for unit tests
TEST_MEDIA_FILES: Dict[str, str] = {
    "duplicate_photo.jpg": "F:/test/photos/duplicate_photo.jpg",
    "unique_photo.png": "F:/test/photos/unique_photo.png",
    "duplicate_video.mp4": "F:/test/videos/duplicate_video.mp4"
}

# Test supported extensions
TEST_EXTENSIONS: List[str] = [
    "jpg", "jpeg", "png", "gif", "bmp",
    "mp4", "mov", "avi", "mkv",
    "nef", "cr2", "arw", "dng"
]

# Mock values for testing (not real)
TEST_API_KEY: str = "test_api_key_not_real"
TEST_SECRET: str = "test_secret_not_real"