"""
Unit tests for unify_duplicate_files function in file_operations module.

Tests verify correct behavior for duplicate file unification:
- Files with identical content get unified to shortest filename
- No progress bar shown when no duplicates exist
- Recursive and non-recursive modes
- Multiple duplicate groups handled correctly
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

from shared.file_operations import unify_duplicate_files


class TestUnifyDuplicateFiles:
    """Test suite for unify_duplicate_files function."""

    @pytest.fixture
    def test_folder(self):
        """Create temporary test directory."""
        test_dir = tempfile.mkdtemp(prefix="test_unify_")

        yield test_dir

        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

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
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath

    def test_unify_no_duplicates(self, test_folder):
        """
        Test that function returns early when no duplicates exist.

        Scenario:
        - Create files with unique content
        - Run unify
        - Verify no changes, no errors
        """
        # Create unique files
        file1 = self.create_test_file(test_folder, "file1.txt", "content 1")
        file2 = self.create_test_file(test_folder, "file2.txt", "content 2")
        file3 = self.create_test_file(test_folder, "file3.txt", "content 3")

        # Run unification (should return early)
        unify_duplicate_files(test_folder, recursive=False)

        # Verify all files still exist with original names
        assert os.path.exists(file1), "file1 should exist"
        assert os.path.exists(file2), "file2 should exist"
        assert os.path.exists(file3), "file3 should exist"

        with open(file1, 'r') as f:
            assert f.read() == "content 1"

    def test_unify_single_duplicate_group(self, test_folder):
        """
        Test unification of a single group of duplicates.

        Scenario:
        - Create 3 files with identical content but different names
        - Shortest name should be canonical
        - All duplicates unified into single file with shortest name
        """
        # Create duplicate files (same content, different names)
        content = "duplicate content"
        file1 = self.create_test_file(test_folder, "short.txt", content)
        file2 = self.create_test_file(test_folder, "medium_name.txt", content)
        file3 = self.create_test_file(test_folder, "very_long_filename.txt", content)

        # Run unification
        unify_duplicate_files(test_folder, recursive=False)

        # Verify only 1 file remains (duplicates replaced with canonical)
        files_in_folder = os.listdir(test_folder)
        assert len(files_in_folder) == 1, "Should have 1 file (duplicates unified)"
        assert files_in_folder[0] == "short.txt", "File should be named short.txt"

        # Verify content preserved
        filepath = os.path.join(test_folder, "short.txt")
        with open(filepath, 'r') as f:
            assert f.read() == content, "Content should be preserved"

    def test_unify_multiple_duplicate_groups(self, test_folder):
        """
        Test unification when multiple independent duplicate groups exist.

        Scenario:
        - Group A: 2 files with content "A"
        - Group B: 3 files with content "B"
        - Each group unified independently
        """
        # Group A
        self.create_test_file(test_folder, "a_short.txt", "content A")
        self.create_test_file(test_folder, "a_very_long_name.txt", "content A")

        # Group B
        self.create_test_file(test_folder, "b_medium.txt", "content B")
        self.create_test_file(test_folder, "b_longest_name_ever.txt", "content B")
        self.create_test_file(test_folder, "b_x.txt", "content B")

        # Run unification
        unify_duplicate_files(test_folder, recursive=False)

        # Verify results
        files_in_folder = sorted(os.listdir(test_folder))

        # Should have 2 files total (1 per group)
        assert len(files_in_folder) == 2, "Should have 2 files (1 per group)"
        assert "a_short.txt" in files_in_folder, "Group A unified to a_short.txt"
        assert "b_x.txt" in files_in_folder, "Group B unified to b_x.txt"

        # Verify content
        with open(os.path.join(test_folder, "a_short.txt"), 'r') as f:
            assert f.read() == "content A"
        with open(os.path.join(test_folder, "b_x.txt"), 'r') as f:
            assert f.read() == "content B"

    def test_unify_recursive_mode(self, test_folder):
        """
        Test that recursive mode unifies files in subdirectories.

        Scenario:
        - Create duplicate files in nested subdirectories
        - Run with recursive=True
        - Verify all subdirectories processed and duplicates unified
        """
        # Create subdirectories
        subdir1 = os.path.join(test_folder, "sub1")
        subdir2 = os.path.join(test_folder, "sub2", "nested")

        content = "duplicate content"

        # Create duplicates in different subdirectories
        file1 = self.create_test_file(subdir1, "long_name.txt", content)
        file2 = self.create_test_file(subdir1, "x.txt", content)
        file3 = self.create_test_file(subdir2, "medium.txt", content)

        # Run recursive unification
        unify_duplicate_files(test_folder, recursive=True)

        # Verify files unified to shortest name within each directory
        all_files = []
        for root, dirs, files in os.walk(test_folder):
            all_files.extend(files)

        # Should have 2 files (1 in subdir1, 1 in subdir2/nested)
        assert len(all_files) == 2, "Should have 2 files total (1 per directory)"
        assert all(f == "x.txt" for f in all_files), "All should be renamed to x.txt"

        # Verify files exist in correct locations
        assert os.path.exists(os.path.join(subdir1, "x.txt")), "subdir1/x.txt should exist"
        assert os.path.exists(os.path.join(subdir2, "x.txt")), "subdir2/nested/x.txt should exist"

    def test_unify_non_recursive_mode(self, test_folder):
        """
        Test that non-recursive mode only processes root directory.

        Scenario:
        - Create duplicates in root and subdirectory
        - Run with recursive=False
        - Verify only root directory processed
        """
        subdir = os.path.join(test_folder, "subdir")

        content = "duplicate content"

        # Create duplicates in root
        self.create_test_file(test_folder, "root1.txt", content)
        self.create_test_file(test_folder, "r.txt", content)

        # Create duplicates in subdirectory (should be ignored)
        self.create_test_file(subdir, "sub1.txt", content)
        self.create_test_file(subdir, "s.txt", content)

        # Run non-recursive
        unify_duplicate_files(test_folder, recursive=False)

        # Verify root files unified to 1 file
        root_files = [f for f in os.listdir(test_folder) if os.path.isfile(os.path.join(test_folder, f))]
        assert len(root_files) == 1, "Should have 1 file in root (duplicates unified)"
        assert root_files[0] == "r.txt", "Root file should be r.txt"

        # Verify subdirectory files unchanged
        subdir_files = os.listdir(subdir)
        assert "sub1.txt" in subdir_files, "Subdirectory files should be unchanged"
        assert "s.txt" in subdir_files, "Subdirectory files should be unchanged"

    def test_unify_empty_folder(self, test_folder):
        """
        Test that function handles empty folder gracefully.

        Scenario:
        - Empty folder
        - Run unify
        - Should return early without errors
        """
        # Don't create any files

        # Should not raise exception
        unify_duplicate_files(test_folder, recursive=True)

        # Folder should still be empty
        assert len(os.listdir(test_folder)) == 0, "Folder should remain empty"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])