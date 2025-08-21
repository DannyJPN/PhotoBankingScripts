"""
Unit tests for createbatchlib.constants module - default values validation.

Tests the validation and accessibility of default configuration values.
"""

import unittest
import os
from typing import Dict, Any

from createbatchlib.constants import (
    DEFAULT_PHOTO_CSV_FILE,
    DEFAULT_PROCESSED_MEDIA_FOLDER,
    DEFAULT_EXIF_FOLDER,
    LOG_DIR,
    STATUS_FIELD_KEYWORD,
    PREPARED_STATUS_VALUE
)


class TestConstantsDefaultValuesValidation(unittest.TestCase):
    """Test default values in constants module."""

    def test_constants__default_photo_csv_file__is_string(self) -> None:
        """Test that DEFAULT_PHOTO_CSV_FILE is a string."""
        self.assertIsInstance(DEFAULT_PHOTO_CSV_FILE, str)
        self.assertTrue(len(DEFAULT_PHOTO_CSV_FILE) > 0)

    def test_constants__default_processed_media_folder__is_string(self) -> None:
        """Test that DEFAULT_PROCESSED_MEDIA_FOLDER is a string."""
        self.assertIsInstance(DEFAULT_PROCESSED_MEDIA_FOLDER, str)
        self.assertTrue(len(DEFAULT_PROCESSED_MEDIA_FOLDER) > 0)

    def test_constants__default_exif_folder__is_string(self) -> None:
        """Test that DEFAULT_EXIF_FOLDER is a string."""
        self.assertIsInstance(DEFAULT_EXIF_FOLDER, str)
        self.assertTrue(len(DEFAULT_EXIF_FOLDER) > 0)

    def test_constants__log_dir__is_string(self) -> None:
        """Test that LOG_DIR is a string."""
        self.assertIsInstance(LOG_DIR, str)
        self.assertTrue(len(LOG_DIR) > 0)

    def test_constants__status_field_keyword__is_valid(self) -> None:
        """Test that STATUS_FIELD_KEYWORD is valid."""
        self.assertIsInstance(STATUS_FIELD_KEYWORD, str)
        self.assertEqual(STATUS_FIELD_KEYWORD, "status")

    def test_constants__prepared_status_value__is_valid(self) -> None:
        """Test that PREPARED_STATUS_VALUE is valid."""
        self.assertIsInstance(PREPARED_STATUS_VALUE, str)
        self.assertEqual(PREPARED_STATUS_VALUE, "připraveno")

    def test_constants__paths_are_absolute__validation(self) -> None:
        """Test that path constants are absolute paths."""
        self.assertTrue(os.path.isabs(DEFAULT_PHOTO_CSV_FILE))
        self.assertTrue(os.path.isabs(DEFAULT_PROCESSED_MEDIA_FOLDER))
        self.assertTrue(os.path.isabs(DEFAULT_EXIF_FOLDER))
        self.assertTrue(os.path.isabs(LOG_DIR))


if __name__ == "__main__":
    unittest.main()