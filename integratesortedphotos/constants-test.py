"""
Test-specific constants for IntegrateSortedPhotos module.

This module provides test-only values as required by CLAUDE.md global rules.
"""

# Test directories - safe paths for testing
TEST_SORTED_FOLDER: str = "F:/Dropbox/Scripts/Python/Fotobanking/integratesortedphotos/tests/data/sorted"
TEST_TARGET_FOLDER: str = "F:/Dropbox/Scripts/Python/Fotobanking/integratesortedphotos/tests/data/target"
TEST_LOG_DIR: str = "F:/Dropbox/Scripts/Python/Fotobanking/integratesortedphotos/tests/logs"

# Test-only configuration
TEST_LOG_LEVEL: str = "DEBUG"

# Test file patterns for unit tests
TEST_PHOTO_FILES: dict[str, str] = {
    "photo1.jpg": "F:/test/photos/photo1.jpg",
    "photo2.png": "F:/test/photos/photo2.png",
    "photo3.raw": "F:/test/photos/photo3.raw",
}

# Mock values for testing (not real)
TEST_API_KEY: str = "test_api_key_not_real"
TEST_SECRET: str = "test_secret_not_real"
