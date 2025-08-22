"""
Test-specific constants for CreateBatch module.

This module provides test-only values as required by CLAUDE.md global rules.
"""

# Test directories - safe paths for testing
TEST_PHOTO_CSV_FILE: str = "F:/Dropbox/Scripts/Python/Fotobanking/createbatch/tests/data/test_photos.csv"
TEST_OUTPUT_FOLDER: str = "F:/Dropbox/Scripts/Python/Fotobanking/createbatch/tests/data/output"
TEST_EXIF_FOLDER: str = "F:/Dropbox/Scripts/Python/Fotobanking/createbatch/tests/data/exif"
TEST_LOG_FOLDER: str = "F:/Dropbox/Scripts/Python/Fotobanking/createbatch/tests/logs"

# Test-only configuration
TEST_LOG_LEVEL: str = "DEBUG"

# Test file patterns for unit tests
TEST_MEDIA_FILES: dict[str, str] = {
    "test_photo1.jpg": "F:/test/photos/test_photo1.jpg",
    "test_photo2.png": "F:/test/photos/test_photo2.png",
    "test_video1.mp4": "F:/test/videos/test_video1.mp4",
}

# Test CSV data
TEST_CSV_HEADERS: list[str] = ["file_name", "title", "description", "keywords", "category", "status"]

# Mock values for testing (not real)
TEST_API_KEY: str = "test_api_key_not_real"
TEST_SECRET: str = "test_secret_not_real"
