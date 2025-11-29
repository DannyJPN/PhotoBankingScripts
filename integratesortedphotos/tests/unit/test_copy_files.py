"""
Unit tests for copy_files module.

This module contains comprehensive tests for the memory-efficient file copying
functions, including generator-based streaming and progress estimation.
"""

import os
import tempfile
import shutil
import unittest
from pathlib import Path

# Add parent directory to path for imports
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from integratesortedphotoslib.copy_files import (
    generate_file_pairs,
    estimate_file_count,
    copy_files_streaming,
    copy_files_with_progress_estimation,
    copy_files_with_preserved_dates,
)


class TestGenerateFilePairs(unittest.TestCase):
    """Test suite for generate_file_pairs generator function."""

    def setUp(self):
        """Set up test fixtures with temporary directories and files."""
        self.temp_dir = tempfile.mkdtemp()
        self.src_folder = os.path.join(self.temp_dir, "source")
        self.dest_folder = os.path.join(self.temp_dir, "destination")
        os.makedirs(self.src_folder)

    def tearDown(self):
        """Clean up temporary test directories."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_generate_file_pairs__empty_directory__returns_no_pairs(self):
        """Test that empty directory generates no file pairs."""
        pairs = list(generate_file_pairs(self.src_folder, self.dest_folder))
        self.assertEqual(len(pairs), 0)

    def test_generate_file_pairs__single_file__returns_one_pair(self):
        """Test that single file generates one correct pair."""
        test_file = os.path.join(self.src_folder, "test.txt")
        Path(test_file).touch()

        pairs = list(generate_file_pairs(self.src_folder, self.dest_folder))

        self.assertEqual(len(pairs), 1)
        src, dest = pairs[0]
        self.assertEqual(src, test_file)
        self.assertTrue(dest.startswith(self.dest_folder))
        self.assertTrue(dest.endswith("test.txt"))

    def test_generate_file_pairs__nested_files__preserves_structure(self):
        """Test that nested directory structure is preserved in pairs."""
        # Create nested structure
        nested_dir = os.path.join(self.src_folder, "subdir1", "subdir2")
        os.makedirs(nested_dir)
        file1 = os.path.join(self.src_folder, "root.txt")
        file2 = os.path.join(nested_dir, "nested.txt")
        Path(file1).touch()
        Path(file2).touch()

        pairs = list(generate_file_pairs(self.src_folder, self.dest_folder))

        self.assertEqual(len(pairs), 2)

        # Check that relative paths are preserved
        src_paths = [src for src, _ in pairs]

        self.assertIn(file1, src_paths)
        self.assertIn(file2, src_paths)

        # Verify destination paths maintain structure
        for src, dest in pairs:
            rel_path = os.path.relpath(src, self.src_folder)
            expected_dest = os.path.join(self.dest_folder, rel_path)
            self.assertEqual(dest, expected_dest)

    def test_generate_file_pairs__multiple_files__returns_all_pairs(self):
        """Test that multiple files all generate correct pairs."""
        num_files = 50
        for i in range(num_files):
            Path(os.path.join(self.src_folder, f"file_{i}.txt")).touch()

        pairs = list(generate_file_pairs(self.src_folder, self.dest_folder))

        self.assertEqual(len(pairs), num_files)

    def test_generate_file_pairs__is_generator__not_list(self):
        """Test that function returns a generator, not a list."""
        result = generate_file_pairs(self.src_folder, self.dest_folder)
        self.assertTrue(hasattr(result, "__iter__"))
        self.assertTrue(hasattr(result, "__next__"))


class TestEstimateFileCount(unittest.TestCase):
    """Test suite for estimate_file_count function."""

    def setUp(self):
        """Set up test fixtures with temporary directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.src_folder = os.path.join(self.temp_dir, "source")
        os.makedirs(self.src_folder)

    def tearDown(self):
        """Clean up temporary test directories."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_estimate_file_count__empty_directory__returns_zero(self):
        """Test that empty directory returns zero estimate."""
        count = estimate_file_count(self.src_folder)
        self.assertEqual(count, 0)

    def test_estimate_file_count__small_directory__returns_accurate_count(self):
        """Test that small directory returns reasonably accurate count."""
        # Create 10 files
        for i in range(10):
            Path(os.path.join(self.src_folder, f"file_{i}.txt")).touch()

        count = estimate_file_count(self.src_folder, sample_size=100)
        # Should be close to 10 (exact for small directories)
        self.assertGreaterEqual(count, 5)  # Allow some variance
        self.assertLessEqual(count, 15)

    def test_estimate_file_count__nested_structure__estimates_total(self):
        """Test that nested structure provides reasonable estimate."""
        # Create nested structure with consistent file count
        for i in range(5):
            subdir = os.path.join(self.src_folder, f"subdir_{i}")
            os.makedirs(subdir)
            for j in range(3):
                Path(os.path.join(subdir, f"file_{j}.txt")).touch()

        count = estimate_file_count(self.src_folder, sample_size=10)
        # Should estimate around 15 files (5 dirs * 3 files)
        self.assertGreater(count, 0)

    def test_estimate_file_count__custom_sample_size__uses_limit(self):
        """Test that custom sample size is respected."""
        # Create many directories
        for i in range(20):
            subdir = os.path.join(self.src_folder, f"subdir_{i}")
            os.makedirs(subdir)
            Path(os.path.join(subdir, "file.txt")).touch()

        # Small sample size should still work
        count = estimate_file_count(self.src_folder, sample_size=5)
        self.assertGreater(count, 0)


class TestCopyFilesStreaming(unittest.TestCase):
    """Test suite for copy_files_streaming function."""

    def setUp(self):
        """Set up test fixtures with temporary directories and files."""
        self.temp_dir = tempfile.mkdtemp()
        self.src_folder = os.path.join(self.temp_dir, "source")
        self.dest_folder = os.path.join(self.temp_dir, "destination")
        os.makedirs(self.src_folder)

    def tearDown(self):
        """Clean up temporary test directories."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_copy_files_streaming__empty_directory__succeeds(self):
        """Test that copying empty directory succeeds without errors."""
        copy_files_streaming(self.src_folder, self.dest_folder)
        self.assertTrue(os.path.exists(self.dest_folder))

    def test_copy_files_streaming__single_file__copies_successfully(self):
        """Test that single file is copied successfully."""
        test_file = os.path.join(self.src_folder, "test.txt")
        test_content = "Hello, World!"
        with open(test_file, "w") as f:
            f.write(test_content)

        copy_files_streaming(self.src_folder, self.dest_folder)

        dest_file = os.path.join(self.dest_folder, "test.txt")
        self.assertTrue(os.path.exists(dest_file))
        with open(dest_file, "r") as f:
            self.assertEqual(f.read(), test_content)

    def test_copy_files_streaming__multiple_files__copies_all(self):
        """Test that multiple files are all copied."""
        num_files = 10
        for i in range(num_files):
            with open(os.path.join(self.src_folder, f"file_{i}.txt"), "w") as f:
                f.write(f"Content {i}")

        copy_files_streaming(self.src_folder, self.dest_folder)

        # Verify all files copied
        for i in range(num_files):
            dest_file = os.path.join(self.dest_folder, f"file_{i}.txt")
            self.assertTrue(os.path.exists(dest_file))

    def test_copy_files_streaming__nested_structure__preserves_hierarchy(self):
        """Test that nested directory structure is preserved."""
        nested_dir = os.path.join(self.src_folder, "sub1", "sub2")
        os.makedirs(nested_dir)
        nested_file = os.path.join(nested_dir, "nested.txt")
        with open(nested_file, "w") as f:
            f.write("Nested content")

        copy_files_streaming(self.src_folder, self.dest_folder)

        dest_nested = os.path.join(self.dest_folder, "sub1", "sub2", "nested.txt")
        self.assertTrue(os.path.exists(dest_nested))
        with open(dest_nested, "r") as f:
            self.assertEqual(f.read(), "Nested content")

    def test_copy_files_streaming__overwrite_false__skips_existing(self):
        """Test that overwrite=False skips existing files."""
        test_file = os.path.join(self.src_folder, "test.txt")
        with open(test_file, "w") as f:
            f.write("Original content")

        # First copy
        copy_files_streaming(self.src_folder, self.dest_folder, overwrite=False)

        # Modify source
        with open(test_file, "w") as f:
            f.write("Modified content")

        # Second copy with overwrite=False
        copy_files_streaming(self.src_folder, self.dest_folder, overwrite=False)

        # Destination should still have original content
        dest_file = os.path.join(self.dest_folder, "test.txt")
        with open(dest_file, "r") as f:
            self.assertEqual(f.read(), "Original content")

    def test_copy_files_streaming__overwrite_true__replaces_existing(self):
        """Test that overwrite=True replaces existing files."""
        test_file = os.path.join(self.src_folder, "test.txt")
        with open(test_file, "w") as f:
            f.write("Original content")

        # First copy
        copy_files_streaming(self.src_folder, self.dest_folder, overwrite=True)

        # Modify source
        with open(test_file, "w") as f:
            f.write("Modified content")

        # Second copy with overwrite=True
        copy_files_streaming(self.src_folder, self.dest_folder, overwrite=True)

        # Destination should have modified content
        dest_file = os.path.join(self.dest_folder, "test.txt")
        with open(dest_file, "r") as f:
            self.assertEqual(f.read(), "Modified content")

    def test_copy_files_streaming__creates_destination_directory(self):
        """Test that destination directory is created if it doesn't exist."""
        # Don't create dest_folder beforehand
        shutil.rmtree(self.dest_folder, ignore_errors=True)

        test_file = os.path.join(self.src_folder, "test.txt")
        Path(test_file).touch()

        copy_files_streaming(self.src_folder, self.dest_folder)

        self.assertTrue(os.path.exists(self.dest_folder))


class TestCopyFilesWithProgressEstimation(unittest.TestCase):
    """Test suite for copy_files_with_progress_estimation function."""

    def setUp(self):
        """Set up test fixtures with temporary directories and files."""
        self.temp_dir = tempfile.mkdtemp()
        self.src_folder = os.path.join(self.temp_dir, "source")
        self.dest_folder = os.path.join(self.temp_dir, "destination")
        os.makedirs(self.src_folder)

    def tearDown(self):
        """Clean up temporary test directories."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_copy_with_estimation__small_directory__copies_all_files(self):
        """Test that small directory is copied successfully with estimation."""
        for i in range(5):
            with open(os.path.join(self.src_folder, f"file_{i}.txt"), "w") as f:
                f.write(f"Content {i}")

        copy_files_with_progress_estimation(self.src_folder, self.dest_folder)

        # Verify all files copied
        for i in range(5):
            dest_file = os.path.join(self.dest_folder, f"file_{i}.txt")
            self.assertTrue(os.path.exists(dest_file))

    def test_copy_with_estimation__custom_sample_size__works(self):
        """Test that custom sample size parameter works."""
        for i in range(10):
            with open(os.path.join(self.src_folder, f"file_{i}.txt"), "w") as f:
                f.write(f"Content {i}")

        copy_files_with_progress_estimation(self.src_folder, self.dest_folder, sample_size=3)

        # Verify files copied
        for i in range(10):
            dest_file = os.path.join(self.dest_folder, f"file_{i}.txt")
            self.assertTrue(os.path.exists(dest_file))


class TestCopyFilesWithPreservedDates(unittest.TestCase):
    """Test suite for legacy copy_files_with_preserved_dates function."""

    def setUp(self):
        """Set up test fixtures with temporary directories and files."""
        self.temp_dir = tempfile.mkdtemp()
        self.src_folder = os.path.join(self.temp_dir, "source")
        self.dest_folder = os.path.join(self.temp_dir, "destination")
        os.makedirs(self.src_folder)

    def tearDown(self):
        """Clean up temporary test directories."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_legacy_function__works_with_streaming(self):
        """Test that legacy function still works using new streaming approach."""
        test_file = os.path.join(self.src_folder, "test.txt")
        with open(test_file, "w") as f:
            f.write("Test content")

        copy_files_with_preserved_dates(self.src_folder, self.dest_folder)

        dest_file = os.path.join(self.dest_folder, "test.txt")
        self.assertTrue(os.path.exists(dest_file))

    def test_legacy_function__preserves_backward_compatibility(self):
        """Test that legacy function signature is still compatible."""
        # Create test files
        for i in range(3):
            Path(os.path.join(self.src_folder, f"file_{i}.txt")).touch()

        # Should work with just two arguments (old signature)
        copy_files_with_preserved_dates(self.src_folder, self.dest_folder)

        # Verify files copied
        self.assertEqual(len(os.listdir(self.dest_folder)), 3)


if __name__ == "__main__":
    unittest.main()
