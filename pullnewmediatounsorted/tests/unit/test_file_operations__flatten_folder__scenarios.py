"""
Unit tests for flatten_folder function in file_operations module.

Tests verify correct behavior for folder flattening:
- Files moved from subdirectories to root
- Empty subdirectories removed
- Identical files (by hash) deduplicated instead of renamed
- Different files with same name get numeric suffixes
- Hash comparison failures fall back to rename
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

from shared.file_operations import flatten_folder


class TestFlattenFolder:
    """Test suite for flatten_folder function."""

    @pytest.fixture
    def test_folder(self):
        """Create temporary test directory."""
        test_dir = tempfile.mkdtemp(prefix="test_flatten_")

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

    def test_flatten_basic(self, test_folder):
        """
        Test basic flattening of nested files.

        Scenario:
        - Create files in subdirectories
        - Flatten
        - All files should be in root, subdirectories removed
        """
        # Create nested structure
        self.create_test_file(os.path.join(test_folder, "sub1"), "file1.txt", "content 1")
        self.create_test_file(os.path.join(test_folder, "sub2", "nested"), "file2.txt", "content 2")
        self.create_test_file(os.path.join(test_folder, "sub3"), "file3.txt", "content 3")

        # Flatten
        flatten_folder(test_folder)

        # Verify all files in root
        root_files = [f for f in os.listdir(test_folder) if os.path.isfile(os.path.join(test_folder, f))]
        assert len(root_files) == 3, "Should have 3 files in root"
        assert "file1.txt" in root_files
        assert "file2.txt" in root_files
        assert "file3.txt" in root_files

        # Verify no subdirectories remain
        subdirs = [d for d in os.listdir(test_folder) if os.path.isdir(os.path.join(test_folder, d))]
        assert len(subdirs) == 0, "No subdirectories should remain"

        # Verify content preserved
        with open(os.path.join(test_folder, "file1.txt"), 'r') as f:
            assert f.read() == "content 1"

    def test_flatten_identical_files_deduplicated(self, test_folder):
        """
        Test that identical files are deduplicated instead of renamed.

        Scenario:
        - Create identical file in multiple subdirectories (same name, same content)
        - Flatten
        - Should have only 1 file in root (duplicates deleted)
        """
        content = "identical content"

        # Create identical files in different subdirectories
        self.create_test_file(os.path.join(test_folder, "sub1"), "photo.jpg", content)
        self.create_test_file(os.path.join(test_folder, "sub2"), "photo.jpg", content)
        self.create_test_file(os.path.join(test_folder, "sub3"), "photo.jpg", content)

        # Flatten
        flatten_folder(test_folder)

        # Verify only 1 file remains (duplicates deleted)
        root_files = os.listdir(test_folder)
        assert len(root_files) == 1, "Should have only 1 file (duplicates deleted)"
        assert root_files[0] == "photo.jpg", "File should be named photo.jpg"

        # Verify content correct
        with open(os.path.join(test_folder, "photo.jpg"), 'r') as f:
            assert f.read() == content

    def test_flatten_different_files_same_name_renamed(self, test_folder):
        """
        Test that different files with same name get numeric suffixes.

        Scenario:
        - Create files with same name but different content in subdirectories
        - Flatten
        - Should have multiple files with numeric suffixes (_001, _002, etc.)
        """
        # Create different files with same name
        self.create_test_file(os.path.join(test_folder, "sub1"), "file.txt", "content A")
        self.create_test_file(os.path.join(test_folder, "sub2"), "file.txt", "content B")
        self.create_test_file(os.path.join(test_folder, "sub3"), "file.txt", "content C")

        # Flatten
        flatten_folder(test_folder)

        # Verify 3 files with different names
        root_files = sorted(os.listdir(test_folder))
        assert len(root_files) == 3, "Should have 3 files (different content)"

        # Should have file.txt, file_001.txt, file_002.txt
        assert "file.txt" in root_files
        assert "file_001.txt" in root_files
        assert "file_002.txt" in root_files

        # Verify all have different content
        contents = set()
        for filename in root_files:
            with open(os.path.join(test_folder, filename), 'r') as f:
                contents.add(f.read())

        assert contents == {"content A", "content B", "content C"}

    def test_flatten_mixed_identical_and_different(self, test_folder):
        """
        Test flattening with mix of identical and different files.

        Scenario:
        - 2 identical files named photo1.jpg
        - 2 different files named photo2.jpg
        - Result: 1 photo1.jpg, 2 photo2 files (photo2.jpg + photo2_001.jpg)
        """
        # Identical files
        self.create_test_file(os.path.join(test_folder, "sub1"), "photo1.jpg", "identical A")
        self.create_test_file(os.path.join(test_folder, "sub2"), "photo1.jpg", "identical A")

        # Different files
        self.create_test_file(os.path.join(test_folder, "sub3"), "photo2.jpg", "different A")
        self.create_test_file(os.path.join(test_folder, "sub4"), "photo2.jpg", "different B")

        # Flatten
        flatten_folder(test_folder)

        # Verify results
        root_files = sorted(os.listdir(test_folder))
        assert len(root_files) == 3, "Should have 3 files"

        # Should have: photo1.jpg, photo2.jpg, photo2_001.jpg
        assert "photo1.jpg" in root_files, "Should have 1 photo1.jpg (duplicate deleted)"
        assert "photo2.jpg" in root_files
        assert "photo2_001.jpg" in root_files, "Should have photo2_001.jpg (different content)"

        # Verify photo1 content
        with open(os.path.join(test_folder, "photo1.jpg"), 'r') as f:
            assert f.read() == "identical A"

        # Verify photo2 files have different content
        with open(os.path.join(test_folder, "photo2.jpg"), 'r') as f:
            content1 = f.read()
        with open(os.path.join(test_folder, "photo2_001.jpg"), 'r') as f:
            content2 = f.read()

        assert content1 != content2, "photo2 files should have different content"
        assert {content1, content2} == {"different A", "different B"}

    def test_flatten_already_flat(self, test_folder):
        """
        Test that flattening already flat folder is no-op.

        Scenario:
        - All files already in root
        - Flatten
        - No changes
        """
        # Create files in root only
        self.create_test_file(test_folder, "file1.txt", "content 1")
        self.create_test_file(test_folder, "file2.txt", "content 2")

        # Flatten
        flatten_folder(test_folder)

        # Verify files unchanged
        root_files = sorted(os.listdir(test_folder))
        assert root_files == ["file1.txt", "file2.txt"]

    def test_flatten_preserves_root_files(self, test_folder):
        """
        Test that files already in root are preserved.

        Scenario:
        - Files in root + files in subdirectories
        - Flatten
        - Root files unchanged, subdirectory files moved
        """
        # Root files
        self.create_test_file(test_folder, "root1.txt", "root content 1")
        self.create_test_file(test_folder, "root2.txt", "root content 2")

        # Subdirectory files
        self.create_test_file(os.path.join(test_folder, "sub1"), "sub1.txt", "sub content 1")
        self.create_test_file(os.path.join(test_folder, "sub2"), "sub2.txt", "sub content 2")

        # Flatten
        flatten_folder(test_folder)

        # Verify all 4 files in root
        root_files = sorted(os.listdir(test_folder))
        assert len(root_files) == 4
        assert "root1.txt" in root_files
        assert "root2.txt" in root_files
        assert "sub1.txt" in root_files
        assert "sub2.txt" in root_files

        # Verify root files content unchanged
        with open(os.path.join(test_folder, "root1.txt"), 'r') as f:
            assert f.read() == "root content 1"

    def test_flatten_removes_empty_subdirectories(self, test_folder):
        """
        Test that empty subdirectories are removed after flattening.

        Scenario:
        - Create nested empty directories
        - Flatten
        - All empty directories removed
        """
        # Create nested structure with one file
        os.makedirs(os.path.join(test_folder, "sub1", "nested", "deep"))
        os.makedirs(os.path.join(test_folder, "sub2"))
        self.create_test_file(os.path.join(test_folder, "sub1", "nested", "deep"), "file.txt", "content")

        # Flatten
        flatten_folder(test_folder)

        # Verify file in root
        assert "file.txt" in os.listdir(test_folder)

        # Verify no subdirectories remain
        subdirs = [d for d in os.listdir(test_folder) if os.path.isdir(os.path.join(test_folder, d))]
        assert len(subdirs) == 0, "All subdirectories should be removed"

    def test_flatten_case_insensitive_collision(self, test_folder):
        """
        Test handling of case-insensitive filename collisions (Windows compatibility).

        Scenario:
        - Create file.txt and FILE.txt in different subdirectories (same content)
        - On Windows, these collide (case-insensitive filesystem)
        - Should be deduplicated (identical content)
        """
        content = "same content"

        # Create case-variant files with same content
        self.create_test_file(os.path.join(test_folder, "sub1"), "file.txt", content)
        self.create_test_file(os.path.join(test_folder, "sub2"), "FILE.txt", content)

        # Flatten
        flatten_folder(test_folder)

        # Verify only 1 file (duplicate deleted)
        root_files = os.listdir(test_folder)
        assert len(root_files) == 1, "Should have 1 file (case-insensitive duplicate deleted)"

        # Content should be correct
        filepath = os.path.join(test_folder, root_files[0])
        with open(filepath, 'r') as f:
            assert f.read() == content


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])