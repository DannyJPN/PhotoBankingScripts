"""
Unit tests for move_file function in file_operations module.

Tests verify correct behavior for file moving operations including:
- Successful file moves
- Overwrite behavior (enabled/disabled)
- Error handling for permission errors and missing files
- Directory creation when destination folder doesn't exist
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.file_operations import move_file


class TestMoveFile:
    """Test suite for move_file function."""

    @pytest.fixture
    def test_folders(self):
        """Create temporary test directories."""
        source_dir = tempfile.mkdtemp(prefix="test_move_source_")
        dest_dir = tempfile.mkdtemp(prefix="test_move_dest_")

        yield source_dir, dest_dir

        # Cleanup
        shutil.rmtree(source_dir, ignore_errors=True)
        shutil.rmtree(dest_dir, ignore_errors=True)

    def create_test_file(self, directory: str, filename: str, content: str) -> str:
        """
        Create a test file with specific content.

        Args:
            directory: Directory to create file in
            filename: Name of the file
            content: Content to write to file

        Returns:
            Full path to created file
        """
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath

    def test_move_file_basic(self, test_folders):
        """
        Test basic file move operation.

        Scenario:
        - Create source file
        - Move to destination
        - Verify source no longer exists, destination has correct content
        """
        source_dir, dest_dir = test_folders

        # Create source file
        source_file = self.create_test_file(source_dir, "test.txt", "test content")
        dest_file = os.path.join(dest_dir, "test.txt")

        # Move file
        move_file(source_file, dest_file)

        # Verify
        assert not os.path.exists(source_file), "Source file should no longer exist"
        assert os.path.exists(dest_file), "Destination file should exist"

        with open(dest_file, 'r') as f:
            assert f.read() == "test content", "Destination file should have correct content"

    def test_move_file_creates_directory(self, test_folders):
        """
        Test that move_file creates destination directory if it doesn't exist.

        Scenario:
        - Create source file
        - Move to non-existent subdirectory
        - Verify directory is created and file is moved
        """
        source_dir, dest_dir = test_folders

        # Create source file
        source_file = self.create_test_file(source_dir, "test.txt", "test content")

        # Destination in non-existent subdirectory
        dest_file = os.path.join(dest_dir, "subdir", "nested", "test.txt")

        # Move file
        move_file(source_file, dest_file)

        # Verify directory was created
        assert os.path.exists(os.path.dirname(dest_file)), "Destination directory should be created"
        assert os.path.exists(dest_file), "Destination file should exist"

        with open(dest_file, 'r') as f:
            assert f.read() == "test content", "Content should be correct"

    def test_move_file_overwrite_disabled(self, test_folders):
        """
        Test that move_file skips when destination exists and overwrite=False.

        Scenario:
        - Create source and destination files with different content
        - Move with overwrite=False
        - Verify destination unchanged, source still exists
        """
        source_dir, dest_dir = test_folders

        # Create files
        source_file = self.create_test_file(source_dir, "test.txt", "source content")
        dest_file = self.create_test_file(dest_dir, "test.txt", "dest content")

        # Move with overwrite=False (early return expected)
        move_file(source_file, dest_file, overwrite=False)

        # Verify both files still exist with original content
        assert os.path.exists(source_file), "Source file should still exist"
        assert os.path.exists(dest_file), "Destination file should still exist"

        with open(dest_file, 'r') as f:
            assert f.read() == "dest content", "Destination should be unchanged"

        with open(source_file, 'r') as f:
            assert f.read() == "source content", "Source should be unchanged"

    def test_move_file_overwrite_enabled(self, test_folders):
        """
        Test that move_file replaces destination when overwrite=True.

        Scenario:
        - Create source and destination files with different content
        - Move with overwrite=True
        - Verify destination has source content, source no longer exists
        """
        source_dir, dest_dir = test_folders

        # Create files
        source_file = self.create_test_file(source_dir, "test.txt", "source content")
        dest_file = self.create_test_file(dest_dir, "test.txt", "dest content")

        # Move with overwrite=True
        move_file(source_file, dest_file, overwrite=True)

        # Verify source moved to destination
        assert not os.path.exists(source_file), "Source file should no longer exist"
        assert os.path.exists(dest_file), "Destination file should exist"

        with open(dest_file, 'r') as f:
            assert f.read() == "source content", "Destination should have source content"

    def test_move_file_source_not_exist(self, test_folders):
        """
        Test that move_file raises exception when source doesn't exist.

        Scenario:
        - Attempt to move non-existent file
        - Verify exception is raised
        """
        source_dir, dest_dir = test_folders

        source_file = os.path.join(source_dir, "nonexistent.txt")
        dest_file = os.path.join(dest_dir, "test.txt")

        # Should raise exception
        with pytest.raises(Exception):
            move_file(source_file, dest_file)

    def test_move_file_preserves_metadata(self, test_folders):
        """
        Test that move_file preserves file metadata (modification time).

        Scenario:
        - Create file with specific mtime
        - Move file
        - Verify mtime is preserved
        """
        source_dir, dest_dir = test_folders

        # Create file
        source_file = self.create_test_file(source_dir, "test.txt", "content")

        # Set specific modification time
        import time
        old_time = time.time() - 86400  # 1 day ago
        os.utime(source_file, (old_time, old_time))
        original_mtime = os.path.getmtime(source_file)

        # Move file
        dest_file = os.path.join(dest_dir, "test.txt")
        move_file(source_file, dest_file)

        # Verify mtime preserved (with small tolerance for filesystem precision)
        dest_mtime = os.path.getmtime(dest_file)
        assert abs(dest_mtime - original_mtime) < 1, "Modification time should be preserved"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])