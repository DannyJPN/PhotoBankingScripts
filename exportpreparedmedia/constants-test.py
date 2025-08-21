"""
Test-specific constants for ExportPreparedMedia module.

This module provides test-only values as required by CLAUDE.md global rules.
"""

from typing import Dict, List

# Test directories - safe paths for testing
TEST_PHOTO_CSV: str = "F:/Dropbox/Scripts/Python/Fotobanking/exportpreparedmedia/tests/data/test_photos.csv"
TEST_OUTPUT_FOLDER: str = "F:/Dropbox/Scripts/Python/Fotobanking/exportpreparedmedia/tests/data/output"
TEST_LOG_FOLDER: str = "F:/Dropbox/Scripts\Python/Fotobanking/exportpreparedmedia/tests/logs"

# Test-only configuration
TEST_LOG_LEVEL: str = "DEBUG"
TEST_USERNAME: str = "TestUser"
TEST_COPYRIGHT_AUTHOR: str = "Test Author"
TEST_LOCATION: str = "Test Location"

# Test photobanks
TEST_PHOTOBANKS: List[str] = [
    "shutterstock",
    "adobestock", 
    "dreamstime"
]

# Mock values for testing (not real)
TEST_API_KEY: str = "test_api_key_not_real"
TEST_SECRET: str = "test_secret_not_real"