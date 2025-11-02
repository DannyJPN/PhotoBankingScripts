"""
Unit tests for companion_file_finder module.
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path

from sortunsortedmedialib.companion_file_finder import (
    find_jpg_equivalent,
    find_original_file,
    extract_metadata_from_path
)


class TestCompanionFileFinder(unittest.TestCase):
    """Test companion file finding functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory structure
        self.test_dir = tempfile.mkdtemp()

        # Create structure: Foto/JPG/Category/Year/Month/Camera/
        self.jpg_path = os.path.join(
            self.test_dir, 'Foto', 'JPG', 'Příroda', '2024', '10', 'Canon EOS R5'
        )
        os.makedirs(self.jpg_path, exist_ok=True)

        # Create structure for PNG
        self.png_path = os.path.join(
            self.test_dir, 'Foto', 'PNG', 'Příroda', '2024', '10', 'Canon EOS R5'
        )
        os.makedirs(self.png_path, exist_ok=True)

        # Create structure for edited photos
        self.edited_path = os.path.join(
            self.test_dir, 'Upravené Foto', 'JPG', 'Město', '2024', '9', 'Nikon Z50'
        )
        os.makedirs(self.edited_path, exist_ok=True)

        # Create structure for videos
        self.video_path = os.path.join(
            self.test_dir, 'Video', 'MP4', 'Akce', '2024', '8', 'DJI Mavic'
        )
        os.makedirs(self.video_path, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_find_jpg_equivalent__exists(self):
        """Test finding JPG equivalent when it exists."""
        # Create JPG file
        jpg_file = os.path.join(self.jpg_path, 'IMG_1234.JPG')
        Path(jpg_file).touch()

        # Search for PNG's JPG equivalent
        result = find_jpg_equivalent('IMG_1234.PNG', self.test_dir)

        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), 'IMG_1234.JPG')
        self.assertTrue(os.path.exists(result))

    def test_find_jpg_equivalent__not_exists(self):
        """Test finding JPG equivalent when it doesn't exist."""
        result = find_jpg_equivalent('IMG_9999.PNG', self.test_dir)

        self.assertIsNone(result)

    def test_find_jpg_equivalent__case_insensitive(self):
        """Test finding JPG with different case extensions."""
        # Create jpg file (lowercase)
        jpg_file = os.path.join(self.jpg_path, 'IMG_5678.jpg')
        Path(jpg_file).touch()

        result = find_jpg_equivalent('IMG_5678.RAW', self.test_dir)

        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), 'IMG_5678.jpg')

    def test_find_original_file__photo_exists(self):
        """Test finding original photo for edited version."""
        # Create original JPG
        original_file = os.path.join(self.jpg_path, 'IMG_1234.JPG')
        Path(original_file).touch()

        # Search for edited version's original
        result = find_original_file('IMG_1234_bw.JPG', self.test_dir, is_video=False)

        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), 'IMG_1234.JPG')

    def test_find_original_file__photo_not_exists(self):
        """Test finding original photo when it doesn't exist."""
        result = find_original_file('IMG_9999_edited.JPG', self.test_dir, is_video=False)

        self.assertIsNone(result)

    def test_find_original_file__video_exists(self):
        """Test finding original video for edited version."""
        # Create original video
        original_file = os.path.join(self.video_path, 'VID_5678.MP4')
        Path(original_file).touch()

        # Search for edited version's original
        result = find_original_file('VID_5678_cut.MP4', self.test_dir, is_video=True)

        self.assertIsNotNone(result)
        self.assertEqual(os.path.basename(result), 'VID_5678.MP4')

    def test_extract_metadata_from_path__foto_jpg(self):
        """Test extracting metadata from Foto/JPG path."""
        test_path = os.path.join(
            self.test_dir, 'Foto', 'JPG', 'Příroda', '2024', '10', 'Canon EOS R5', 'IMG_1234.JPG'
        )

        metadata = extract_metadata_from_path(test_path)

        self.assertEqual(metadata['category'], 'Příroda')
        self.assertEqual(metadata['camera_name'], 'Canon EOS R5')
        self.assertEqual(metadata['year'], '2024')
        self.assertEqual(metadata['month'], '10')

    def test_extract_metadata_from_path__upravene_foto(self):
        """Test extracting metadata from Upravené Foto path."""
        test_path = os.path.join(
            self.test_dir, 'Upravené Foto', 'JPG', 'Město', '2024', '9', 'Nikon Z50', 'IMG_5678_bw.JPG'
        )

        metadata = extract_metadata_from_path(test_path)

        self.assertEqual(metadata['category'], 'Město')
        self.assertEqual(metadata['camera_name'], 'Nikon Z50')
        self.assertEqual(metadata['year'], '2024')
        self.assertEqual(metadata['month'], '9')

    def test_extract_metadata_from_path__video(self):
        """Test extracting metadata from Video path."""
        test_path = os.path.join(
            self.test_dir, 'Video', 'MP4', 'Akce', '2024', '8', 'DJI Mavic', 'VID_1234.MP4'
        )

        metadata = extract_metadata_from_path(test_path)

        self.assertEqual(metadata['category'], 'Akce')
        self.assertEqual(metadata['camera_name'], 'DJI Mavic')
        self.assertEqual(metadata['year'], '2024')
        self.assertEqual(metadata['month'], '8')

    def test_extract_metadata_from_path__invalid_path(self):
        """Test extracting metadata from invalid path returns defaults."""
        test_path = "/some/random/path/file.jpg"

        metadata = extract_metadata_from_path(test_path)

        self.assertEqual(metadata['category'], 'Ostatní')
        self.assertEqual(metadata['camera_name'], 'Unknown')


if __name__ == '__main__':
    unittest.main()