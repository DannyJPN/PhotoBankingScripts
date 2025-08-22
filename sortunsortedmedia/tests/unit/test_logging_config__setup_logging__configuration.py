"""
Unit tests for logging configuration setup_logging function.

:author: SortUnsortedMedia Test Suite
:date: 2025-08-21
"""

import unittest
import logging
import tempfile
import json
import os
from unittest.mock import patch, mock_open, MagicMock
from shared.logging_config import setup_logging


class TestLoggingConfigSetupLoggingConfiguration(unittest.TestCase):
    """Test setup_logging configuration functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_color_config = {
            "DEBUG": "cyan",
            "INFO": "green", 
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red"
        }
        self.test_log_file = "test_logfile.log"
        
    def tearDown(self) -> None:
        """Clean up test fixtures."""
        # Reset logging to avoid interference between tests
        logging.getLogger().handlers.clear()
        
        # Clean up test log file if it exists
        if os.path.exists(self.test_log_file):
            try:
                os.remove(self.test_log_file)
            except OSError:
                pass

    @patch('shared.logging_config.open', new_callable=mock_open)
    @patch('shared.logging_config.json.load')
    def test_logging_config__setup_logging__loads_color_configuration(self, mock_json_load: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that setup_logging loads color configuration from JSON."""
        mock_json_load.return_value = self.test_color_config
        
        setup_logging(debug=False, log_file=self.test_log_file)
        
        mock_file_open.assert_called_once()
        mock_json_load.assert_called_once()

    @patch('shared.logging_config.open', side_effect=FileNotFoundError("Color config not found"))
    @patch('shared.logging_config.logging.error')
    def test_logging_config__setup_logging__handles_missing_color_config(self, mock_log_error: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that setup_logging handles missing color configuration file."""
        with self.assertRaises(FileNotFoundError):
            setup_logging(debug=False, log_file=self.test_log_file)
            
        mock_log_error.assert_called_once()

    @patch('shared.logging_config.open', new_callable=mock_open, read_data='invalid json')
    @patch('shared.logging_config.json.load', side_effect=json.JSONDecodeError("Invalid JSON", "doc", 0))
    @patch('shared.logging_config.logging.error')
    def test_logging_config__setup_logging__handles_invalid_color_config(self, mock_log_error: MagicMock, mock_json_load: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that setup_logging handles invalid JSON in color configuration."""
        with self.assertRaises(json.JSONDecodeError):
            setup_logging(debug=False, log_file=self.test_log_file)
            
        mock_log_error.assert_called_once()

    @patch('shared.logging_config.open', new_callable=mock_open)
    @patch('shared.logging_config.json.load')
    def test_logging_config__setup_logging__sets_debug_level_when_debug_true(self, mock_json_load: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that setup_logging sets DEBUG level when debug=True."""
        mock_json_load.return_value = self.test_color_config
        
        setup_logging(debug=True, log_file=self.test_log_file)
        
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.DEBUG, "Should set DEBUG level when debug=True")

    @patch('shared.logging_config.open', new_callable=mock_open)
    @patch('shared.logging_config.json.load')
    def test_logging_config__setup_logging__sets_info_level_when_debug_false(self, mock_json_load: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that setup_logging sets INFO level when debug=False."""
        mock_json_load.return_value = self.test_color_config
        
        setup_logging(debug=False, log_file=self.test_log_file)
        
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.INFO, "Should set INFO level when debug=False")

    @patch('shared.logging_config.open', new_callable=mock_open)
    @patch('shared.logging_config.json.load')
    def test_logging_config__setup_logging__creates_console_and_file_handlers(self, mock_json_load: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that setup_logging creates both console and file handlers."""
        mock_json_load.return_value = self.test_color_config
        
        setup_logging(debug=False, log_file=self.test_log_file)
        
        root_logger = logging.getLogger()
        handlers = root_logger.handlers
        
        # Should have exactly 2 handlers
        self.assertEqual(len(handlers), 2, "Should create exactly 2 handlers")
        
        # Check handler types
        handler_types = [type(handler).__name__ for handler in handlers]
        self.assertIn('StreamHandler', handler_types, "Should have a StreamHandler for console output")
        self.assertIn('FileHandler', handler_types, "Should have a FileHandler for file output")

    @patch('shared.logging_config.open', new_callable=mock_open)
    @patch('shared.logging_config.json.load')
    def test_logging_config__setup_logging__removes_existing_handlers(self, mock_json_load: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that setup_logging removes existing handlers before adding new ones."""
        mock_json_load.return_value = self.test_color_config
        
        # Add a dummy handler first
        root_logger = logging.getLogger()
        dummy_handler = logging.StreamHandler()
        root_logger.addHandler(dummy_handler)
        initial_handler_count = len(root_logger.handlers)
        
        setup_logging(debug=False, log_file=self.test_log_file)
        
        # Should have exactly 2 handlers (console + file), not more
        self.assertEqual(len(root_logger.handlers), 2, "Should replace existing handlers with exactly 2 new ones")

    @patch('shared.logging_config.open', new_callable=mock_open)
    @patch('shared.logging_config.json.load')
    @patch('shared.logging_config.colorlog.ColoredFormatter')
    def test_logging_config__setup_logging__uses_colorlog_formatter(self, mock_colored_formatter: MagicMock, mock_json_load: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that setup_logging uses colorlog.ColoredFormatter."""
        mock_json_load.return_value = self.test_color_config
        
        setup_logging(debug=False, log_file=self.test_log_file)
        
        # ColoredFormatter should be called once and reused for both handlers
        self.assertEqual(mock_colored_formatter.call_count, 1, "Should create one ColoredFormatter instance for both handlers")

    @patch('shared.logging_config.open', new_callable=mock_open)
    @patch('shared.logging_config.json.load')
    def test_logging_config__setup_logging__uses_custom_log_format(self, mock_json_load: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that setup_logging uses the expected log format."""
        mock_json_load.return_value = self.test_color_config
        
        with patch('shared.logging_config.colorlog.ColoredFormatter') as mock_formatter:
            setup_logging(debug=False, log_file=self.test_log_file)
            
            # Check that ColoredFormatter was called with expected format
            expected_format = '%(log_color)s%(levelname)s: %(message)s'
            mock_formatter.assert_called_with(
                expected_format,
                log_colors=self.test_color_config
            )

    @patch('shared.logging_config.open', new_callable=mock_open)
    @patch('shared.logging_config.json.load')
    @patch('shared.logging_config.logging.debug')
    def test_logging_config__setup_logging__logs_completion_message(self, mock_log_debug: MagicMock, mock_json_load: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that setup_logging logs completion message."""
        mock_json_load.return_value = self.test_color_config
        
        setup_logging(debug=True, log_file=self.test_log_file)  # debug=True to enable debug logging
        
        mock_log_debug.assert_called_once()
        args = mock_log_debug.call_args[0]
        self.assertIn("Logging setup complete", args[0], "Should log completion message")
        self.assertIn(self.test_log_file, args[0], "Should include log file path in completion message")

    @patch('shared.logging_config.open', new_callable=mock_open)
    @patch('shared.logging_config.json.load')
    def test_logging_config__setup_logging__function_signature_validation(self, mock_json_load: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that function signature matches expected interface."""
        import inspect
        
        sig = inspect.signature(setup_logging)
        params = sig.parameters
        
        self.assertIn('debug', params, "Function should have 'debug' parameter")
        self.assertIn('log_file', params, "Function should have 'log_file' parameter")
        
        # Check default values
        self.assertEqual(params['debug'].default, False, "debug parameter should default to False")
        self.assertEqual(params['log_file'].default, "logs/logfile.log", "log_file should have expected default")

    @patch('shared.logging_config.open', new_callable=mock_open)
    @patch('shared.logging_config.json.load')  
    def test_logging_config__setup_logging__multiple_calls_handling(self, mock_json_load: MagicMock, mock_file_open: MagicMock) -> None:
        """Test that multiple calls to setup_logging work correctly."""
        mock_json_load.return_value = self.test_color_config
        
        # First call
        setup_logging(debug=False, log_file="first.log")
        first_handler_count = len(logging.getLogger().handlers)
        
        # Second call
        setup_logging(debug=True, log_file="second.log")
        second_handler_count = len(logging.getLogger().handlers)
        
        # Should have same number of handlers (old ones removed, new ones added)
        self.assertEqual(first_handler_count, 2, "First call should create 2 handlers")
        self.assertEqual(second_handler_count, 2, "Second call should maintain 2 handlers")


if __name__ == "__main__":
    unittest.main()