"""
Unit tests for removealreadysortedoutlib.constants module - default values validation.
"""

import unittest

from removealreadysortedoutlib.constants import DEFAULT_LOG_DIR, DEFAULT_TARGET_FOLDER, DEFAULT_UNSORTED_FOLDER


class TestConstantsDefaultValuesValidation(unittest.TestCase):
    """Test default values in constants module."""

    def test_constants__default_unsorted_folder__is_string(self) -> None:
        """Test that DEFAULT_UNSORTED_FOLDER is a string."""
        self.assertIsInstance(DEFAULT_UNSORTED_FOLDER, str)
        self.assertTrue(len(DEFAULT_UNSORTED_FOLDER) > 0)

    def test_constants__default_target_folder__is_string(self) -> None:
        """Test that DEFAULT_TARGET_FOLDER is a string."""
        self.assertIsInstance(DEFAULT_TARGET_FOLDER, str)
        self.assertTrue(len(DEFAULT_TARGET_FOLDER) > 0)

    def test_constants__default_log_dir__is_string(self) -> None:
        """Test that DEFAULT_LOG_DIR is a string."""
        self.assertIsInstance(DEFAULT_LOG_DIR, str)
        self.assertTrue(len(DEFAULT_LOG_DIR) > 0)


if __name__ == "__main__":
    unittest.main()
