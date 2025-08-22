"""
Unit tests for givephotobankreadymediafileslib.constants module - default values validation.
"""

import unittest

from givephotobankreadymediafileslib.constants import (
    DEFAULT_CATEGORIES_CSV,
    DEFAULT_INTERVAL,
    DEFAULT_LOG_DIR,
    DEFAULT_MEDIA_CSV,
    DEFAULT_TRAINING_DATA_DIR,
)


class TestConstantsDefaultValuesValidation(unittest.TestCase):
    """Test default values in constants module."""

    def test_constants__default_media_csv__is_string(self) -> None:
        """Test that DEFAULT_MEDIA_CSV is a string."""
        self.assertIsInstance(DEFAULT_MEDIA_CSV, str)
        self.assertTrue(len(DEFAULT_MEDIA_CSV) > 0)

    def test_constants__default_categories_csv__is_string(self) -> None:
        """Test that DEFAULT_CATEGORIES_CSV is a string."""
        self.assertIsInstance(DEFAULT_CATEGORIES_CSV, str)
        self.assertTrue(len(DEFAULT_CATEGORIES_CSV) > 0)

    def test_constants__default_training_data_dir__is_string(self) -> None:
        """Test that DEFAULT_TRAINING_DATA_DIR is a string."""
        self.assertIsInstance(DEFAULT_TRAINING_DATA_DIR, str)
        self.assertTrue(len(DEFAULT_TRAINING_DATA_DIR) > 0)

    def test_constants__default_log_dir__is_string(self) -> None:
        """Test that DEFAULT_LOG_DIR is a string."""
        self.assertIsInstance(DEFAULT_LOG_DIR, str)
        self.assertTrue(len(DEFAULT_LOG_DIR) > 0)

    def test_constants__default_interval__is_positive_integer(self) -> None:
        """Test that DEFAULT_INTERVAL is a positive integer."""
        self.assertIsInstance(DEFAULT_INTERVAL, int)
        self.assertGreater(DEFAULT_INTERVAL, 0)


if __name__ == "__main__":
    unittest.main()
