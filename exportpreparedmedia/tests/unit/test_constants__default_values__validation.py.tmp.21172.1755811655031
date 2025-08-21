"""
Unit tests for exportpreparedmedialib.constants module - default values validation.
"""

import unittest
import os

from exportpreparedmedialib.constants import (
    DEFAULT_PHOTO_CSV,
    DEFAULT_OUTPUT_FOLDER,
    DEFAULT_LOCATION,
    DEFAULT_USERNAME,
    DEFAULT_COPYRIGHT_AUTHOR
)


class TestConstantsDefaultValuesValidation(unittest.TestCase):
    """Test default values in constants module."""

    def test_constants__default_photo_csv__is_string(self) -> None:
        """Test that DEFAULT_PHOTO_CSV is a string."""
        self.assertIsInstance(DEFAULT_PHOTO_CSV, str)
        self.assertTrue(len(DEFAULT_PHOTO_CSV) > 0)

    def test_constants__default_output_folder__is_string(self) -> None:
        """Test that DEFAULT_OUTPUT_FOLDER is a string."""
        self.assertIsInstance(DEFAULT_OUTPUT_FOLDER, str)
        self.assertTrue(len(DEFAULT_OUTPUT_FOLDER) > 0)

    def test_constants__default_location__is_string(self) -> None:
        """Test that DEFAULT_LOCATION is a string."""
        self.assertIsInstance(DEFAULT_LOCATION, str)
        self.assertEqual(DEFAULT_LOCATION, "Czech republic")

    def test_constants__default_username__is_string(self) -> None:
        """Test that DEFAULT_USERNAME is a string."""
        self.assertIsInstance(DEFAULT_USERNAME, str)
        self.assertTrue(len(DEFAULT_USERNAME) > 0)

    def test_constants__default_copyright_author__is_string(self) -> None:
        """Test that DEFAULT_COPYRIGHT_AUTHOR is a string."""
        self.assertIsInstance(DEFAULT_COPYRIGHT_AUTHOR, str)
        self.assertTrue(len(DEFAULT_COPYRIGHT_AUTHOR) > 0)


if __name__ == "__main__":
    unittest.main()