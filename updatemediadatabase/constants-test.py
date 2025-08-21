"""
Test-specific constants for UpdateMediaDatabase module.

This module provides test-only values as required by CLAUDE.md global rules.
"""

from typing import Dict, List

# Test directories - safe paths for testing
TEST_PHOTO_CSV: str = "F:/Dropbox/Scripts/Python/Fotobanking/updatemediadatabase/tests/data/test_photos.csv"
TEST_LIMIT_CSV: str = "F:/Dropbox/Scripts/Python/Fotobanking/updatemediadatabase/tests/data/test_limits.csv"
TEST_PHOTO_DIR: str = "F:/Dropbox/Scripts/Python/Fotobanking/updatemediadatabase/tests/data/photos"
TEST_VIDEO_DIR: str = "F:/Dropbox/Scripts/Python/Fotobanking/updatemediadatabase/tests/data/videos"
TEST_LOG_DIR: str = "F:/Dropbox/Scripts/Python/Fotobanking/updatemediadatabase/tests/logs"
TEST_EXIFTOOL_DIR: str = "F:/Dropbox/Scripts/Python/Fotobanking/updatemediadatabase/tests/data/exiftool"

# Test-only configuration
TEST_LOG_LEVEL: str = "DEBUG"

# Test file patterns for unit tests
TEST_MEDIA_FILES: Dict[str, str] = {
    "test_photo1.jpg": "F:/test/photos/test_photo1.jpg",
    "test_video1.mp4": "F:/test/videos/test_video1.mp4",
    "test_raw1.nef": "F:/test/photos/test_raw1.nef"
}

# Test database columns
TEST_CSV_COLUMNS: List[str] = [
    "file_name",
    "title",
    "description",
    "keywords",
    "category",
    "width",
    "height",
    "create_date",
    "status"
]

# Mock values for testing (not real)
TEST_API_KEY: str = "test_api_key_not_real"
TEST_SECRET: str = "test_secret_not_real"