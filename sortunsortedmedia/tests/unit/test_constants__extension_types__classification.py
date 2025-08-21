"""
Unit tests for file extension classification in constants module.

:author: SortUnsortedMedia Test Suite
:date: 2025-08-21
"""

import unittest
from sortunsortedmedialib.constants import EXTENSION_TYPES


class TestExtensionTypesClassification(unittest.TestCase):
    """Test file extension classification."""

    def test_constants__extension_types__photo_standard_formats(self) -> None:
        """Test standard photo format classification."""
        photo_extensions = ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp"]
        
        for ext in photo_extensions:
            with self.subTest(extension=ext):
                self.assertIn(ext, EXTENSION_TYPES, f"Extension {ext} should be in EXTENSION_TYPES")
                self.assertEqual(EXTENSION_TYPES[ext], "Foto", f"Extension {ext} should be classified as Foto")

    def test_constants__extension_types__photo_raw_formats(self) -> None:
        """Test RAW photo format classification."""
        raw_extensions = ["raw", "dng", "arw", "cr2", "cr3", "nef", "orf", "rw2"]
        
        for ext in raw_extensions:
            with self.subTest(extension=ext):
                self.assertIn(ext, EXTENSION_TYPES, f"RAW extension {ext} should be in EXTENSION_TYPES")
                self.assertEqual(EXTENSION_TYPES[ext], "Foto", f"RAW extension {ext} should be classified as Foto")

    def test_constants__extension_types__video_standard_formats(self) -> None:
        """Test standard video format classification."""
        video_extensions = ["mp4", "mov", "avi", "wmv", "mkv", "webm", "m4v", "3gp"]
        
        for ext in video_extensions:
            with self.subTest(extension=ext):
                self.assertIn(ext, EXTENSION_TYPES, f"Video extension {ext} should be in EXTENSION_TYPES")
                self.assertEqual(EXTENSION_TYPES[ext], "Video", f"Extension {ext} should be classified as Video")

    def test_constants__extension_types__video_professional_formats(self) -> None:
        """Test professional video format classification."""
        pro_video_extensions = ["mxf", "braw", "prores", "dnxhd", "dnxhr", "xavc"]
        
        for ext in pro_video_extensions:
            with self.subTest(extension=ext):
                self.assertIn(ext, EXTENSION_TYPES, f"Professional video extension {ext} should be in EXTENSION_TYPES")
                self.assertEqual(EXTENSION_TYPES[ext], "Video", f"Professional extension {ext} should be classified as Video")

    def test_constants__extension_types__audio_formats(self) -> None:
        """Test audio format classification."""
        audio_extensions = ["mp3", "wav", "flac", "aac", "ogg", "wma", "m4a", "aiff"]
        
        for ext in audio_extensions:
            with self.subTest(extension=ext):
                self.assertIn(ext, EXTENSION_TYPES, f"Audio extension {ext} should be in EXTENSION_TYPES")
                self.assertEqual(EXTENSION_TYPES[ext], "Audio", f"Extension {ext} should be classified as Audio")

    def test_constants__extension_types__case_sensitivity(self) -> None:
        """Test that extensions are stored in lowercase."""
        for ext in EXTENSION_TYPES.keys():
            with self.subTest(extension=ext):
                self.assertEqual(ext, ext.lower(), f"Extension {ext} should be stored in lowercase")

    def test_constants__extension_types__no_duplicates(self) -> None:
        """Test that there are no duplicate extensions."""
        extensions = list(EXTENSION_TYPES.keys())
        unique_extensions = set(extensions)
        
        self.assertEqual(len(extensions), len(unique_extensions), 
                        "There should be no duplicate extensions in EXTENSION_TYPES")

    def test_constants__extension_types__comprehensive_coverage(self) -> None:
        """Test that major file types are covered."""
        required_photo_formats = ["jpg", "jpeg", "png", "nef", "cr2", "dng"]
        required_video_formats = ["mp4", "mov", "avi"]
        required_audio_formats = ["mp3", "wav", "flac"]
        
        for ext in required_photo_formats:
            with self.subTest(category="photo", extension=ext):
                self.assertIn(ext, EXTENSION_TYPES)
                self.assertEqual(EXTENSION_TYPES[ext], "Foto")
                
        for ext in required_video_formats:
            with self.subTest(category="video", extension=ext):
                self.assertIn(ext, EXTENSION_TYPES)
                self.assertEqual(EXTENSION_TYPES[ext], "Video")
                
        for ext in required_audio_formats:
            with self.subTest(category="audio", extension=ext):
                self.assertIn(ext, EXTENSION_TYPES)
                self.assertEqual(EXTENSION_TYPES[ext], "Audio")

    def test_constants__extension_types__unknown_extension_handling(self) -> None:
        """Test handling of unknown extensions."""
        unknown_extensions = ["xyz", "unknown", "test", "fake"]
        
        for ext in unknown_extensions:
            with self.subTest(extension=ext):
                self.assertNotIn(ext, EXTENSION_TYPES, 
                               f"Unknown extension {ext} should not be in EXTENSION_TYPES")

    def test_constants__extension_types__special_cases(self) -> None:
        """Test special case extensions."""
        # Test that r3d appears in both photo and video (should be one or the other)
        r3d_count = sum(1 for ext, type_ in EXTENSION_TYPES.items() if ext == "r3d")
        self.assertLessEqual(r3d_count, 1, "Extension r3d should appear only once")
        
        # Test that ogg is properly classified (can be video or audio)
        if "ogg" in EXTENSION_TYPES:
            self.assertIn(EXTENSION_TYPES["ogg"], ["Video", "Audio"], 
                         "Extension ogg should be classified as Video or Audio")


if __name__ == "__main__":
    unittest.main()