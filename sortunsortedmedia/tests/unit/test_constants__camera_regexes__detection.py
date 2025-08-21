"""
Unit tests for camera detection regex patterns in constants module.

:author: SortUnsortedMedia Test Suite
:date: 2025-08-21
"""

import unittest
import re
from sortunsortedmedialib.constants import CAMERA_REGEXES


class TestCameraRegexesDetection(unittest.TestCase):
    """Test camera detection regex patterns."""

    def test_constants__camera_regexes__sony_cybershot_detection(self) -> None:
        """Test Sony CyberShot W810 pattern detection."""
        pattern = r"^DSC\d{5}$"
        test_cases = [
            ("DSC00001", True, "Sony CyberShot W810"),
            ("DSC00151", True, "Sony CyberShot W810"),
            ("DSC99999", True, "Sony CyberShot W810"),
            ("DSC0001", False, "Too few digits"),
            ("DSC000001", False, "Too many digits"),
            ("dsc00001", False, "Wrong case"),
            ("DSC00001.JPG", False, "With extension"),
        ]
        
        for filename, should_match, description in test_cases:
            with self.subTest(filename=filename, description=description):
                match = re.match(pattern, filename)
                if should_match:
                    self.assertIsNotNone(match, f"Should match {filename}")
                    self.assertEqual(CAMERA_REGEXES[pattern], "Sony CyberShot W810")
                else:
                    self.assertIsNone(match, f"Should not match {filename}")

    def test_constants__camera_regexes__realme8_detection(self) -> None:
        """Test Realme 8 pattern detection."""
        pattern = r"^IMG\d{14}$"
        test_cases = [
            ("IMG20220423105358", True, "Realme 8"),
            ("IMG12345678901234", True, "Realme 8"),
            ("IMG2022042310535", False, "Too few digits"),
            ("IMG202204231053588", False, "Too many digits"),
            ("img20220423105358", False, "Wrong case"),
            ("IMG20220423105358.jpg", False, "With extension"),
        ]
        
        for filename, should_match, description in test_cases:
            with self.subTest(filename=filename, description=description):
                match = re.match(pattern, filename)
                if should_match:
                    self.assertIsNotNone(match, f"Should match {filename}")
                    self.assertEqual(CAMERA_REGEXES[pattern], "Realme 8")
                else:
                    self.assertIsNone(match, f"Should not match {filename}")

    def test_constants__camera_regexes__samsung_j320fn_detection(self) -> None:
        """Test Samsung J320FN pattern detection."""
        pattern = r"^\d{8}_\d{6}$"
        test_cases = [
            ("20210729_141633", True, "Samsung J320FN"),
            ("12345678_123456", True, "Samsung J320FN"),
            ("2021072_141633", False, "Too few date digits"),
            ("20210729_14163", False, "Too few time digits"),
            ("20210729-141633", False, "Wrong separator"),
            ("20210729_141633.jpg", False, "With extension"),
        ]
        
        for filename, should_match, description in test_cases:
            with self.subTest(filename=filename, description=description):
                match = re.match(pattern, filename)
                if should_match:
                    self.assertIsNotNone(match, f"Should match {filename}")
                    self.assertEqual(CAMERA_REGEXES[pattern], "Samsung J320FN")
                else:
                    self.assertIsNone(match, f"Should not match {filename}")

    def test_constants__camera_regexes__dji_drone_detection(self) -> None:
        """Test DJI Drone pattern detection."""
        pattern = r"^DJI_\d{14}_\d{4}_[WTZN]$"
        test_cases = [
            ("DJI_20250402140705_0008_W", True, "DJI Drone"),
            ("DJI_12345678901234_1234_T", True, "DJI Drone"),
            ("DJI_12345678901234_1234_Z", True, "DJI Drone"),
            ("DJI_12345678901234_1234_N", True, "DJI Drone"),
            ("DJI_1234567890123_1234_W", False, "Too few date digits"),
            ("DJI_12345678901234_123_W", False, "Too few sequence digits"),
            ("DJI_12345678901234_1234_X", False, "Invalid suffix"),
            ("dji_12345678901234_1234_W", False, "Wrong case"),
        ]
        
        for filename, should_match, description in test_cases:
            with self.subTest(filename=filename, description=description):
                match = re.match(pattern, filename)
                if should_match:
                    self.assertIsNotNone(match, f"Should match {filename}")
                    self.assertEqual(CAMERA_REGEXES[pattern], "DJI Drone")
                else:
                    self.assertIsNone(match, f"Should not match {filename}")

    def test_constants__camera_regexes__unknown_pattern_handling(self) -> None:
        """Test handling of unknown filename patterns."""
        unknown_patterns = [
            "unknown_file.jpg",
            "random_123.png",
            "test_file_name.mp4",
            "IMG_20220101_120000.jpg",  # Different format
        ]
        
        for filename in unknown_patterns:
            with self.subTest(filename=filename):
                matched = False
                for pattern in CAMERA_REGEXES.keys():
                    if re.match(pattern, filename):
                        matched = True
                        break
                self.assertFalse(matched, f"Unknown pattern {filename} should not match any regex")

    def test_constants__camera_regexes__all_patterns_compiled(self) -> None:
        """Test that all regex patterns compile successfully."""
        for pattern, camera_name in CAMERA_REGEXES.items():
            with self.subTest(pattern=pattern, camera=camera_name):
                try:
                    compiled_pattern = re.compile(pattern)
                    self.assertIsNotNone(compiled_pattern)
                except re.error as e:
                    self.fail(f"Pattern {pattern} for {camera_name} failed to compile: {e}")


if __name__ == "__main__":
    unittest.main()