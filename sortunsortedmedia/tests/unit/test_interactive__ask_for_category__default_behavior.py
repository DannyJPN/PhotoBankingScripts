"""
Unit tests for interactive module ask_for_category function.

:author: SortUnsortedMedia Test Suite
:date: 2025-08-21
"""

import unittest
import logging
from unittest.mock import patch, MagicMock
from sortunsortedmedialib.interactive import ask_for_category


class TestInteractiveAskForCategoryDefaultBehavior(unittest.TestCase):
    """Test ask_for_category default behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_media_path = "/test/path/to/media.jpg"
        self.test_media_path_video = "/test/path/to/video.mp4"
        self.test_media_path_invalid = ""

    @patch('sortunsortedmedialib.interactive.logging')
    def test_interactive__ask_for_category__returns_default_category(self, mock_logging: MagicMock) -> None:
        """Test that ask_for_category returns default category."""
        result = ask_for_category(self.test_media_path)
        
        self.assertEqual(result, "Ostatní", "Should return default category 'Ostatní'")
        self.assertIsInstance(result, str, "Should return string")

    @patch('sortunsortedmedialib.interactive.logging')
    def test_interactive__ask_for_category__logs_request(self, mock_logging: MagicMock) -> None:
        """Test that ask_for_category logs the request."""
        ask_for_category(self.test_media_path)
        
        mock_logging.info.assert_called_once_with(f"Interactive category request for: {self.test_media_path}")

    @patch('sortunsortedmedialib.interactive.logging')
    def test_interactive__ask_for_category__handles_video_files(self, mock_logging: MagicMock) -> None:
        """Test that ask_for_category handles video files correctly."""
        result = ask_for_category(self.test_media_path_video)
        
        self.assertEqual(result, "Ostatní", "Should return default category for video files")
        mock_logging.info.assert_called_once_with(f"Interactive category request for: {self.test_media_path_video}")

    @patch('sortunsortedmedialib.interactive.logging')
    def test_interactive__ask_for_category__handles_empty_path(self, mock_logging: MagicMock) -> None:
        """Test that ask_for_category handles empty path."""
        result = ask_for_category(self.test_media_path_invalid)
        
        self.assertEqual(result, "Ostatní", "Should return default category even for empty path")
        mock_logging.info.assert_called_once_with(f"Interactive category request for: {self.test_media_path_invalid}")

    @patch('sortunsortedmedialib.interactive.logging')
    def test_interactive__ask_for_category__handles_none_path(self, mock_logging: MagicMock) -> None:
        """Test that ask_for_category handles None path gracefully."""
        # This should potentially raise an exception or handle None gracefully
        # Testing current behavior first, then can improve error handling
        try:
            result = ask_for_category(None)
            # If it doesn't raise an exception, check the result
            self.assertEqual(result, "Ostatní", "Should return default category even for None path")
        except TypeError:
            # If it raises TypeError, that's also acceptable current behavior
            pass

    @patch('sortunsortedmedialib.interactive.logging')
    def test_interactive__ask_for_category__consistent_return_type(self, mock_logging: MagicMock) -> None:
        """Test that ask_for_category always returns consistent type."""
        test_paths = [
            "/test/image.jpg",
            "/test/video.mp4",
            "/test/document.pdf",
            "/very/long/path/to/some/media/file/with/spaces in name.jpg",
            "relative/path.png"
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                result = ask_for_category(path)
                self.assertIsInstance(result, str, f"Should always return string for path: {path}")
                self.assertEqual(result, "Ostatní", f"Should always return 'Ostatní' for path: {path}")

    @patch('sortunsortedmedialib.interactive.logging')
    def test_interactive__ask_for_category__logging_behavior(self, mock_logging: MagicMock) -> None:
        """Test detailed logging behavior."""
        test_path = "/test/detailed/logging.jpg"
        
        # Ensure logging is called correctly
        ask_for_category(test_path)
        
        # Verify logging.info was called exactly once with correct message
        self.assertEqual(mock_logging.info.call_count, 1, "Should call logging.info exactly once")
        args, kwargs = mock_logging.info.call_args
        self.assertEqual(len(args), 1, "Should pass exactly one argument to logging.info")
        self.assertIn(test_path, args[0], "Log message should contain the media path")
        self.assertIn("Interactive category request", args[0], "Log message should contain descriptive text")

    def test_interactive__ask_for_category__function_signature(self) -> None:
        """Test that function signature matches expected interface."""
        import inspect
        
        sig = inspect.signature(ask_for_category)
        params = list(sig.parameters.keys())
        
        self.assertEqual(len(params), 1, "Function should have exactly one parameter")
        self.assertEqual(params[0], "media_path", "Parameter should be named 'media_path'")
        
        # Check return annotation if present
        if sig.return_annotation != inspect.Signature.empty:
            self.assertEqual(sig.return_annotation, str, "Return annotation should be str")

    @patch('sortunsortedmedialib.interactive.logging')
    def test_interactive__ask_for_category__performance_basic(self, mock_logging: MagicMock) -> None:
        """Test basic performance characteristics."""
        import time
        
        start_time = time.time()
        result = ask_for_category(self.test_media_path)
        end_time = time.time()
        
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0, "Function should execute in less than 1 second")
        self.assertEqual(result, "Ostatní", "Should still return correct result")


if __name__ == "__main__":
    unittest.main()