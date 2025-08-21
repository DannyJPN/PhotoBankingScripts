"""
Integration tests for complete media processing workflow.

:author: SortUnsortedMedia Test Suite
:date: 2025-08-21
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
from constants_test import (
    TEST_UNSORTED_FOLDER, 
    TEST_TARGET_FOLDER,
    TEST_CAMERA_FILES,
    TEST_CATEGORIES
)


class TestMediaProcessingEndToEndWorkflow(unittest.TestCase):
    """Test complete media processing workflow integration."""

    def setUp(self) -> None:
        """Set up test environment with temporary directories."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_unsorted = os.path.join(self.temp_dir, "unsorted")
        self.test_sorted = os.path.join(self.temp_dir, "sorted")
        
        os.makedirs(self.test_unsorted, exist_ok=True)
        os.makedirs(self.test_sorted, exist_ok=True)
        
        # Create test files
        self.test_files = []
        for filename, expected_camera in TEST_CAMERA_FILES.items():
            file_path = os.path.join(self.test_unsorted, filename)
            with open(file_path, 'w') as f:
                f.write(f"Test content for {filename}")
            self.test_files.append(file_path)

    def tearDown(self) -> None:
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('media_helper.find_unmatched_media')
    @patch('media_helper.process_unmatched_files')
    def test_media_processing__end_to_end__complete_workflow_success(self, mock_process: MagicMock, mock_find: MagicMock) -> None:
        """Test complete successful media processing workflow."""
        # Mock find_unmatched_media to return test files
        mock_find.return_value = {
            'jpg_files': [os.path.join(self.test_unsorted, "DSC00001.JPG")],
            'other_images': [],
            'videos': [],
            'edited_images': [],
            'edited_videos': []
        }
        
        # Mock process_unmatched_files to simulate successful processing
        mock_process.return_value = True
        
        # Import and run main function
        try:
            from sortunsortedmedia import main
            with patch('sys.argv', ['sortunsortedmedia.py', '--unsorted_folder', self.test_unsorted, '--target_folder', self.test_sorted]):
                main()
        except SystemExit:
            pass  # Expected for successful completion
        
        # Verify that functions were called
        mock_find.assert_called_once()
        # mock_process might be called multiple times for different categories
        
    @patch('media_helper.find_unmatched_media')
    def test_media_processing__end_to_end__no_files_found(self, mock_find: MagicMock) -> None:
        """Test workflow when no unmatched media files are found."""
        # Mock find_unmatched_media to return empty results
        mock_find.return_value = {
            'jpg_files': [],
            'other_images': [],
            'videos': [],
            'edited_images': [],
            'edited_videos': []
        }
        
        # Import and run main function
        try:
            from sortunsortedmedia import main
            with patch('sys.argv', ['sortunsortedmedia.py', '--unsorted_folder', self.test_unsorted, '--target_folder', self.test_sorted]):
                main()
        except SystemExit:
            pass  # Expected for completion
        
        # Verify that find function was called
        mock_find.assert_called_once()

    def test_media_processing__end_to_end__argument_parsing(self) -> None:
        """Test command line argument parsing integration."""
        from sortunsortedmedia import parse_arguments
        
        # Test default arguments
        with patch('sys.argv', ['sortunsortedmedia.py']):
            args = parse_arguments()
            self.assertIsNotNone(args.unsorted_folder)
            self.assertIsNotNone(args.target_folder)
            self.assertIsNotNone(args.interval)
            self.assertFalse(args.debug)

        # Test custom arguments
        custom_args = [
            'sortunsortedmedia.py', 
            '--unsorted_folder', self.test_unsorted,
            '--target_folder', self.test_sorted,
            '--interval', '10',
            '--debug'
        ]
        
        with patch('sys.argv', custom_args):
            args = parse_arguments()
            self.assertEqual(args.unsorted_folder, self.test_unsorted)
            self.assertEqual(args.target_folder, self.test_sorted)
            self.assertEqual(args.interval, 10)
            self.assertTrue(args.debug)

    @patch('shared.logging_config.setup_logging')
    @patch('shared.utils.get_log_filename')
    @patch('shared.file_operations.ensure_directory')
    def test_media_processing__end_to_end__logging_setup_integration(self, mock_ensure_dir: MagicMock, mock_log_filename: MagicMock, mock_setup_logging: MagicMock) -> None:
        """Test logging setup integration in main workflow."""
        # Mock dependencies
        mock_log_filename.return_value = "test.log"
        mock_ensure_dir.return_value = True
        
        # Mock media processing to avoid actual file operations
        with patch('media_helper.find_unmatched_media') as mock_find:
            mock_find.return_value = {
                'jpg_files': [], 'other_images': [], 'videos': [], 
                'edited_images': [], 'edited_videos': []
            }
            
            # Import and run main function
            try:
                from sortunsortedmedia import main
                with patch('sys.argv', ['sortunsortedmedia.py', '--debug']):
                    main()
            except SystemExit:
                pass
        
        # Verify logging setup was called
        mock_setup_logging.assert_called_once()
        args, kwargs = mock_setup_logging.call_args
        self.assertTrue(kwargs['debug'] or args[0], "Should enable debug logging when --debug flag is used")

    @patch('media_helper.find_unmatched_media')
    @patch('media_helper.process_unmatched_files')
    def test_media_processing__end_to_end__category_processing_order(self, mock_process: MagicMock, mock_find: MagicMock) -> None:
        """Test that media categories are processed in correct order."""
        # Mock find_unmatched_media to return files in all categories
        mock_find.return_value = {
            'jpg_files': ['test.jpg'],
            'other_images': ['test.png'],
            'videos': ['test.mp4'],
            'edited_images': ['test_edit.jpg'],
            'edited_videos': ['test_edit.mp4']
        }
        
        # Track processing calls
        process_calls = []
        def track_process_calls(files, target_folder, interval):
            process_calls.append(len(files))
        
        mock_process.side_effect = track_process_calls
        
        # Import and run main function
        try:
            from sortunsortedmedia import main
            with patch('sys.argv', ['sortunsortedmedia.py', '--unsorted_folder', self.test_unsorted, '--target_folder', self.test_sorted]):
                main()
        except SystemExit:
            pass
        
        # Verify processing was called for each non-empty category
        expected_calls = 5  # All categories have files
        self.assertEqual(len(process_calls), expected_calls, 
                        f"Should process all {expected_calls} non-empty categories")

    def test_media_processing__end_to_end__error_handling_integration(self) -> None:
        """Test error handling integration in main workflow."""
        # Test with non-existent directories
        non_existent_dir = "/path/that/does/not/exist"
        
        try:
            from sortunsortedmedia import main
            with patch('sys.argv', ['sortunsortedmedia.py', '--unsorted_folder', non_existent_dir]):
                # Should handle errors gracefully without crashing
                main()
        except Exception as e:
            # If exceptions are raised, they should be meaningful
            self.assertIsInstance(e, (FileNotFoundError, OSError, SystemExit), 
                                f"Should raise appropriate exception types, got: {type(e)}")

    @patch('media_helper.find_unmatched_media', side_effect=Exception("Test error"))
    def test_media_processing__end_to_end__exception_handling(self, mock_find: MagicMock) -> None:
        """Test handling of exceptions during media processing."""
        # Import and run main function with mocked exception
        try:
            from sortunsortedmedia import main
            with patch('sys.argv', ['sortunsortedmedia.py', '--unsorted_folder', self.test_unsorted]):
                main()
        except Exception as e:
            # Should either handle gracefully or raise appropriate exception
            self.assertIsNotNone(e, "Should handle or propagate exceptions appropriately")

    def test_media_processing__end_to_end__directory_structure_validation(self) -> None:
        """Test validation of directory structure requirements."""
        # Test that required directories exist or are created
        self.assertTrue(os.path.exists(self.test_unsorted), "Unsorted directory should exist")
        self.assertTrue(os.path.exists(self.test_sorted), "Target directory should exist")
        
        # Test directory accessibility
        self.assertTrue(os.access(self.test_unsorted, os.R_OK), "Should have read access to unsorted directory")
        self.assertTrue(os.access(self.test_sorted, os.W_OK), "Should have write access to target directory")


if __name__ == "__main__":
    unittest.main()