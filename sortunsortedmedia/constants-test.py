"""
Test-specific constants for SortUnsortedMedia.

This module provides test-only values as required by CLAUDE.md global rules.
"""

from typing import Dict, List

# Test directories - safe paths for testing
TEST_UNSORTED_FOLDER: str = "F:/Dropbox/Scripts/Python/Fotobanking/sortunsortedmedia/tests/data/unsorted"
TEST_TARGET_FOLDER: str = "F:/Dropbox/Scripts/Python/Fotobanking/sortunsortedmedia/tests/data/sorted"
TEST_LOG_FOLDER: str = "F:/Dropbox/Scripts/Python/Fotobanking/sortunsortedmedia/tests/logs"

# Test-only configuration
TEST_INTERVAL: int = 1  # Shorter interval for faster tests
TEST_LOG_LEVEL: str = "DEBUG"

# Test file patterns for unit tests
TEST_CAMERA_FILES: Dict[str, str] = {
    "DSC00001.JPG": "Sony CyberShot W810",
    "IMG20220101120000.jpg": "Realme 8",
    "20210101_120000.jpg": "Samsung J320FN",
    "SAM_0001.JPG": "Samsung ES9",
    "NIK_0001.JPG": "Nikon Z50",
    "DJI_20220101120000_0001_W.JPG": "DJI Drone",
    "PICT0001.JPG": "Bunaty Micro 4K",
    "test_unknown.jpg": "Unknown Camera"
}

# Test file extensions
TEST_EXTENSIONS: Dict[str, str] = {
    "jpg": "Foto",
    "jpeg": "Foto", 
    "png": "Foto",
    "nef": "Foto",
    "mp4": "Video",
    "mov": "Video",
    "mp3": "Audio",
    "unknown": "Unknown"
}

# Test categories
TEST_CATEGORIES: List[str] = [
    "Test_Rodina",
    "Test_Práce",
    "Test_Ostatní"
]

# Mock API keys for testing (not real)
TEST_API_KEY: str = "test_api_key_not_real"
TEST_SECRET: str = "test_secret_not_real"