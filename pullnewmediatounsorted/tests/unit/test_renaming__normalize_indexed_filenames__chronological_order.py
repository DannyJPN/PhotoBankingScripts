"""
Unit tests for chronological sorting in normalize_indexed_filenames function.

Tests verify that files are renumbered in chronological order (oldest first),
ensuring that lower numbers are assigned to older files.
"""

import os
import sys
import tempfile
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pullnewmediatounsortedlib.renaming import normalize_indexed_filenames
from shared.file_operations import compute_file_hash


class TestNormalizeIndexedFilenamesChronologicalOrder:
    """Test suite for chronological ordering in file normalization."""

    @pytest.fixture
    def test_folders(self):
        """Create temporary test directories."""
        source_dir = tempfile.mkdtemp(prefix="test_source_")
        reference_dir = tempfile.mkdtemp(prefix="test_reference_")

        yield source_dir, reference_dir

        # Cleanup
        shutil.rmtree(source_dir, ignore_errors=True)
        shutil.rmtree(reference_dir, ignore_errors=True)

    def create_test_file(self, directory: str, filename: str, content: str, mtime: datetime) -> str:
        """
        Create a test file with specific content and modification time.

        Args:
            directory: Directory to create file in
            filename: Name of the file
            content: Content to write to file
            mtime: Modification time to set

        Returns:
            Full path to created file
        """
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w') as f:
            f.write(content)

        # Set modification time
        timestamp = mtime.timestamp()
        os.utime(filepath, (timestamp, timestamp))

        return filepath

    def test_chronological_ordering_basic(self, test_folders):
        """
        Test that files are numbered chronologically (oldest first).

        Scenario:
        - Create 3 files with different timestamps
        - Older files should get lower numbers
        """
        source_dir, reference_dir = test_folders

        # Create test files with known timestamps
        now = datetime.now()

        # File 1: Oldest (should become PICT000001)
        oldest_file = self.create_test_file(
            source_dir,
            "PICT9999.JPG",
            "oldest content",
            now - timedelta(days=3)
        )

        # File 2: Middle (should become PICT000002)
        middle_file = self.create_test_file(
            source_dir,
            "PICT0001.JPG",
            "middle content",
            now - timedelta(days=2)
        )

        # File 3: Newest (should become PICT000003)
        newest_file = self.create_test_file(
            source_dir,
            "PICT0100.JPG",
            "newest content",
            now - timedelta(days=1)
        )

        # Run normalization
        normalize_indexed_filenames(
            source_folder=source_dir,
            reference_folder=reference_dir,
            prefix="PICT",
            width=6,
            max_number=999999
        )

        # Check resulting filenames
        files_in_dir = sorted(os.listdir(source_dir))

        assert "PICT000001.JPG" in files_in_dir, "Oldest file should be numbered 000001"
        assert "PICT000002.JPG" in files_in_dir, "Middle file should be numbered 000002"
        assert "PICT000003.JPG" in files_in_dir, "Newest file should be numbered 000003"

        # Verify content matches (oldest -> PICT000001)
        with open(os.path.join(source_dir, "PICT000001.JPG"), 'r') as f:
            assert f.read() == "oldest content", "PICT000001 should contain oldest content"

        with open(os.path.join(source_dir, "PICT000002.JPG"), 'r') as f:
            assert f.read() == "middle content", "PICT000002 should contain middle content"

        with open(os.path.join(source_dir, "PICT000003.JPG"), 'r') as f:
            assert f.read() == "newest content", "PICT000003 should contain newest content"

    def test_chronological_ordering_with_reference(self, test_folders):
        """
        Test that existing files in reference folder are preserved.

        Scenario:
        - Reference folder has PICT000001.JPG (existing file)
        - Source has same file (by hash) + new files
        - Existing file should keep its number, new files numbered chronologically
        """
        source_dir, reference_dir = test_folders
        now = datetime.now()

        # Create reference file
        ref_content = "existing reference content"
        ref_file = self.create_test_file(
            reference_dir,
            "PICT000001.JPG",
            ref_content,
            now - timedelta(days=10)
        )

        # Create source files
        # File 1: Same content as reference (should keep PICT000001)
        same_file = self.create_test_file(
            source_dir,
            "PICT9999.JPG",
            ref_content,
            now - timedelta(days=5)
        )

        # File 2: New old file (should become PICT000002)
        old_new_file = self.create_test_file(
            source_dir,
            "PICT0050.JPG",
            "old new content",
            now - timedelta(days=3)
        )

        # File 3: New recent file (should become PICT000003)
        recent_new_file = self.create_test_file(
            source_dir,
            "PICT0200.JPG",
            "recent new content",
            now - timedelta(days=1)
        )

        # Run normalization
        normalize_indexed_filenames(
            source_folder=source_dir,
            reference_folder=reference_dir,
            prefix="PICT",
            width=6,
            max_number=999999
        )

        # Check resulting filenames
        files_in_dir = sorted(os.listdir(source_dir))

        assert "PICT000001.JPG" in files_in_dir, "Reference file should keep its number"
        assert "PICT000002.JPG" in files_in_dir, "Old new file should be 000002"
        assert "PICT000003.JPG" in files_in_dir, "Recent new file should be 000003"

        # Verify content
        with open(os.path.join(source_dir, "PICT000001.JPG"), 'r') as f:
            assert f.read() == ref_content, "PICT000001 should be reference content"

        with open(os.path.join(source_dir, "PICT000002.JPG"), 'r') as f:
            assert f.read() == "old new content", "PICT000002 should be old new content"

        with open(os.path.join(source_dir, "PICT000003.JPG"), 'r') as f:
            assert f.read() == "recent new content", "PICT000003 should be recent new content"

    def test_chronological_ordering_many_files(self, test_folders):
        """
        Test chronological ordering with many files.

        Scenario:
        - Create 10 files with random-looking names but chronological timestamps
        - Verify all are numbered in chronological order
        """
        source_dir, reference_dir = test_folders
        now = datetime.now()

        # Create files with decreasing age (oldest to newest)
        file_data = []
        for i in range(10):
            content = f"content_{i}"
            filename = f"PICT{9000 + i * 100}.JPG"  # Random-looking numbers
            mtime = now - timedelta(days=10 - i)  # Oldest = 10 days ago, newest = 1 day ago

            filepath = self.create_test_file(source_dir, filename, content, mtime)
            file_data.append((content, mtime))

        # Run normalization
        normalize_indexed_filenames(
            source_folder=source_dir,
            reference_folder=reference_dir,
            prefix="PICT",
            width=6,
            max_number=999999
        )

        # Verify files are numbered chronologically
        for i in range(10):
            expected_filename = f"PICT{i+1:06d}.JPG"
            expected_content = f"content_{i}"

            filepath = os.path.join(source_dir, expected_filename)
            assert os.path.exists(filepath), f"{expected_filename} should exist"

            with open(filepath, 'r') as f:
                actual_content = f.read()
                assert actual_content == expected_content, \
                    f"{expected_filename} should contain {expected_content}, got {actual_content}"

    def test_chronological_ordering_same_timestamp(self, test_folders):
        """
        Test handling of files with identical timestamps.

        Scenario:
        - Multiple files created at the same time
        - Should not crash and assign sequential numbers
        """
        source_dir, reference_dir = test_folders
        now = datetime.now()

        # Create 3 files with same timestamp
        for i in range(3):
            self.create_test_file(
                source_dir,
                f"PICT{1000 + i}.JPG",
                f"content_{i}",
                now - timedelta(days=1)
            )

        # Should not crash
        normalize_indexed_filenames(
            source_folder=source_dir,
            reference_folder=reference_dir,
            prefix="PICT",
            width=6,
            max_number=999999
        )

        # All files should be renumbered
        files_in_dir = sorted(os.listdir(source_dir))
        assert len(files_in_dir) == 3, "Should have 3 files"
        assert all("PICT" in f for f in files_in_dir), "All files should have PICT prefix"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])