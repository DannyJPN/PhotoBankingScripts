"""
Unit tests for integratesortedphotoslib.constants module - default values validation.
"""

import unittest

from integratesortedphotoslib.constants import DEFAULT_SORTED_FOLDER, DEFAULT_TARGET_FOLDER, LOG_DIR


class TestConstantsDefaultValuesValidation(unittest.TestCase):
    """Test default values in constants module."""

    def test_constants__default_sorted_folder__is_string(self) -> None:
        """Test that DEFAULT_SORTED_FOLDER is a string."""
        self.assertIsInstance(DEFAULT_SORTED_FOLDER, str)
        self.assertTrue(len(DEFAULT_SORTED_FOLDER) > 0)

    def test_constants__default_target_folder__is_string(self) -> None:
        """Test that DEFAULT_TARGET_FOLDER is a string."""
        self.assertIsInstance(DEFAULT_TARGET_FOLDER, str)
        self.assertTrue(len(DEFAULT_TARGET_FOLDER) > 0)

    def test_constants__log_dir__is_string(self) -> None:
        """Test that LOG_DIR is a string."""
        self.assertIsInstance(LOG_DIR, str)
        self.assertTrue(len(LOG_DIR) > 0)


if __name__ == "__main__":
    unittest.main()
