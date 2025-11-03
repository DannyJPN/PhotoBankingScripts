"""
Unit tests for EXIF camera detector.

Tests the camera detection logic including:
- Encoder tag parsing for DJI drones
- Filename pattern detection for Matrice 300
- DJI Mini 3 detection with specific encoder
- Edge cases and error handling
"""

import unittest
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sortunsortedmedialib.exif_camera_detector import EXIFCameraDetector


class TestEXIFCameraDetector(unittest.TestCase):
    """Test EXIF camera detector functionality."""

    def setUp(self):
        """Set up test detector instance."""
        self.detector = EXIFCameraDetector()

    # === Encoder Tag Detection Tests ===

    def test_encoder_tag__dji_neo__returns_correct_name(self):
        """Test DJI Neo detection via Encoder tag."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="DJI NEO",
            file_path="DJI_20250325145015_0001_D.MP4"
        )
        self.assertEqual(result, "DJI Neo")

    def test_encoder_tag__mavic3__returns_correct_name(self):
        """Test DJI Mavic 3 detection via Encoder tag."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="DJIMavic3",
            file_path="DJI_0994.MOV"
        )
        self.assertEqual(result, "DJI Mavic 3")

    def test_encoder_tag__mavic3_thermal__uses_database_lookup(self):
        """Test Mavic 3 Thermal detection via Encoder tag with database lookup."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="DJI M3T",
            file_path="DJI_20250327215720_0001_S.MP4"
        )
        self.assertEqual(result, "DJI Mavic 3 Thermal")

    # === Matrice 300 Filename Pattern Tests ===

    def test_matrice_300__thermal_suffix__returns_correct_name(self):
        """Test Matrice 300 thermal camera detection via _T suffix."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="Lavf60.3.100",
            file_path="DJI_20250402142155_0014_T.MP4"
        )
        self.assertEqual(result, "DJI Matrice 300 + Zenmuse H20T")

    def test_matrice_300__wide_suffix__returns_correct_name(self):
        """Test Matrice 300 wide camera detection via _W suffix."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="Lavf60.3.100",
            file_path="DJI_20250402141639_0004_W.MP4"
        )
        self.assertEqual(result, "DJI Matrice 300 + Zenmuse H20T")

    def test_matrice_300__zoom_suffix__returns_correct_name(self):
        """Test Matrice 300 zoom camera detection via _Z suffix."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="Lavf60.3.100",
            file_path="DJI_20250402141639_0004_Z.MP4"
        )
        self.assertEqual(result, "DJI Matrice 300 + Zenmuse H20T")

    def test_matrice_300__no_suffix__returns_correct_name(self):
        """Test Matrice 300 wide camera detection without suffix."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="Lavf60.3.100",
            file_path="DJI_20250328142609_0001.MP4"
        )
        self.assertEqual(result, "DJI Matrice 300 + Zenmuse H20T")

    def test_mavic3_thermal__s_suffix__returns_correct_name(self):
        """Test Mavic 3 Thermal detection via _S suffix (fallback)."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="Lavf60.3.100",
            file_path="DJI_20250327215720_0001_S.MP4"
        )
        self.assertEqual(result, "DJI Mavic 3 Thermal")

    # === DJI Mini 3 Detection Tests ===

    def test_mini_3__4digit_filename_lavf_encoder__returns_correct_name(self):
        """Test DJI Mini 3 detection via 4-digit filename + Lavf56.15.102 encoder."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="Lavf56.15.102",
            file_path="DJI_0012.MP4"
        )
        self.assertEqual(result, "DJI Mini 3")

    def test_mini_3__4digit_filename_wrong_encoder__returns_unknown(self):
        """Test 4-digit DJI filename with different encoder returns Unknown."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="Lavf60.3.100",
            file_path="DJI_0012.MP4"
        )
        self.assertEqual(result, "DJI Drone (Unknown Model)")

    # === FC Code Detection Tests ===

    def test_fc_code_detection__fc3682__returns_mini_3(self):
        """Test FC3682 code detection returns Mini 3."""
        result = self.detector._construct_camera_name(
            make="",
            model="FC3682",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "DJI Mini 3")

    def test_fc_code_detection__fc3582__returns_mini_3_pro(self):
        """Test FC3582 code detection returns Mini 3 Pro."""
        result = self.detector._construct_camera_name(
            make="",
            model="FC3582",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "DJI Mini 3 Pro")

    def test_fc_code_detection__fc6520__returns_inspire_2(self):
        """Test FC6520 code detection returns Inspire 2 + X5S."""
        result = self.detector._construct_camera_name(
            make="",
            model="FC6520",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "DJI Inspire 2 + Zenmuse X5S")

    # === DJI Make Tag Tests ===

    def test_make_tag__dji_with_fc_code__returns_correct_name(self):
        """Test DJI Make tag with FC code uses database."""
        result = self.detector._construct_camera_name(
            make="DJI",
            model="FC3582",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "DJI Mini 3 Pro")

    def test_make_tag__dji_without_model__returns_generic(self):
        """Test DJI Make tag without model returns generic name."""
        result = self.detector._construct_camera_name(
            make="DJI",
            model="",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "DJI Drone")

    def test_make_tag__dji_unknown_model__returns_with_model_name(self):
        """Test DJI with unknown model code returns fallback."""
        result = self.detector._construct_camera_name(
            make="DJI",
            model="FC9999",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "DJI Drone (FC9999)")

    # === Priority Tests ===

    def test_priority__encoder_over_fc_code(self):
        """Test that Encoder tag has priority over FC code."""
        result = self.detector._construct_camera_name(
            make="",
            model="FC3582",  # Would give Mini 3 Pro
            software="",
            encoder="DJI NEO",  # Encoder should override
            file_path=""
        )
        self.assertEqual(result, "DJI Neo")

    def test_priority__fc_code_over_filename(self):
        """Test that FC code has priority over filename pattern."""
        result = self.detector._construct_camera_name(
            make="",
            model="FC6520",  # Inspire 2
            software="",
            encoder="",
            file_path="DJI_0012.MP4"  # Would be Mini 3 by filename
        )
        self.assertEqual(result, "DJI Inspire 2 + Zenmuse X5S")

    # === Edge Cases ===

    def test_edge_case__short_filename__returns_none(self):
        """Test that very short filenames don't cause IndexError."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="",
            file_path="D.MP4"
        )
        self.assertIsNone(result)

    def test_edge_case__bounds_check_short_filename__handles_safely(self):
        """Test bounds checking prevents IndexError on short filenames."""
        # This filename matches DJI pattern but is too short for safe indexing
        # The bounds check should prevent IndexError
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="",
            file_path="DJI_T.MP4"  # Only 10 chars, needs at least 8 for suffix check
        )
        # Doesn't match the timestamp regex patterns, falls through
        self.assertIsNone(result)

    def test_edge_case__empty_encoder__handled(self):
        """Test empty encoder string is handled."""
        result = self.detector._construct_camera_name(
            make="DJI",
            model="FC3582",
            software="",
            encoder="",  # Empty encoder
            file_path=""
        )
        self.assertEqual(result, "DJI Mini 3 Pro")

    def test_edge_case__empty_input__returns_none(self):
        """Test that empty input returns None."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="",
            file_path=""
        )
        self.assertIsNone(result)

    # === Other Camera Brands ===

    def test_samsung__sm_prefix__normalizes_correctly(self):
        """Test Samsung SM- prefix is removed."""
        result = self.detector._construct_camera_name(
            make="Samsung",
            model="SM-J320FN",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "Samsung J320FN")

    def test_realme__lowercase_model__capitalizes(self):
        """Test Realme lowercase model is capitalized."""
        result = self.detector._construct_camera_name(
            make="realme",
            model="8",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "Realme 8")

    def test_realme__video_no_exif__filename_based_detection(self):
        """Test Realme 8 video detection via filename when EXIF is missing."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="",
            file_path="VID20240908130819.mp4"
        )
        self.assertEqual(result, "Realme 8")

    def test_realme__video_uppercase_extension__detects(self):
        """Test Realme detection works with uppercase .MP4 extension."""
        result = self.detector._construct_camera_name(
            make="",
            model="",
            software="",
            encoder="",
            file_path="VID20241231235959.MP4"
        )
        self.assertEqual(result, "Realme 8")

    def test_realme__video_with_exif__prefers_exif(self):
        """Test that EXIF detection has priority over filename pattern."""
        result = self.detector._construct_camera_name(
            make="samsung",
            model="SM-G991B",
            software="",
            encoder="",
            file_path="VID20240908130819.mp4"
        )
        # Should return Samsung, not Realme, because Make tag exists
        self.assertEqual(result, "Samsung G991B")

    def test_sony__dsc_prefix__preserved(self):
        """Test Sony DSC prefix is preserved."""
        result = self.detector._construct_camera_name(
            make="SONY",
            model="DSC-W810",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "Sony DSC-W810")

    def test_nikon__normalizes_nikon_prefix(self):
        """Test Nikon normalizes NIKON prefix."""
        result = self.detector._construct_camera_name(
            make="NIKON CORPORATION",
            model="NIKON Z 50",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "Nikon Z 50")

    def test_bunaty__wifi_solar__detected_from_software(self):
        """Test Bunaty WiFi Solar detection from software tag."""
        result = self.detector._construct_camera_name(
            make="Trail camera",
            model="RD7010WF",
            software="Bunaty WiFi",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "Bunaty WiFi Solar")

    def test_bunaty__micro_4k__detected_from_software(self):
        """Test Bunaty Micro 4K detection from software tag."""
        result = self.detector._construct_camera_name(
            make="iCatch",
            model="",
            software="BUNATY_BV18AD_07",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "Bunaty Micro 4K")

    def test_canon__generic__works(self):
        """Test Canon camera detection."""
        result = self.detector._construct_camera_name(
            make="Canon",
            model="EOS 5D Mark IV",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "Canon EOS 5D Mark IV")

    def test_apple__iphone__works(self):
        """Test Apple iPhone detection."""
        result = self.detector._construct_camera_name(
            make="Apple",
            model="iPhone 5s",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "Apple iPhone 5s")

    def test_generic__make_model__combines(self):
        """Test generic make+model returns combined string."""
        result = self.detector._construct_camera_name(
            make="TestBrand",
            model="TestModel",
            software="",
            encoder="",
            file_path=""
        )
        self.assertEqual(result, "TestBrand TestModel")


if __name__ == "__main__":
    unittest.main()