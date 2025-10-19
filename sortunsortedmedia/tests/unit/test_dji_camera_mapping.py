"""
Unit tests for DJI camera mapping database.

Tests the mapping between DJI FC camera codes and drone/camera names.
"""

import unittest
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sortunsortedmedialib.dji_camera_mapping import (
    get_dji_drone_name,
    get_dji_camera_info,
    is_dji_camera,
)


class TestDJICameraMapping(unittest.TestCase):
    """Test DJI camera code to drone name mapping."""

    def test_single_camera_drones__mini_3_pro__returns_correct_name(self):
        """Test Mini 3 Pro detection."""
        result = get_dji_drone_name("FC3582")
        self.assertEqual(result, "DJI Mini 3 Pro")

    def test_single_camera_drones__mini_4_pro__returns_correct_name(self):
        """Test Mini 4 Pro detection."""
        result = get_dji_drone_name("FC3682")
        self.assertEqual(result, "DJI Mini 4 Pro")

    def test_single_camera_drones__mavic_pro__returns_correct_name(self):
        """Test Mavic Pro detection."""
        result = get_dji_drone_name("FC220")
        self.assertEqual(result, "DJI Mavic Pro")

    def test_single_camera_drones__air_2s__returns_correct_name(self):
        """Test Air 2S detection."""
        result = get_dji_drone_name("FC3411")
        self.assertEqual(result, "DJI Air 2S")

    def test_single_camera_drones__phantom_4_pro__returns_correct_name(self):
        """Test Phantom 4 Pro detection."""
        result = get_dji_drone_name("FC6310")
        self.assertEqual(result, "DJI Phantom 4 Pro")

    def test_multi_camera_drones__air_3_wide__returns_correct_name(self):
        """Test Air 3 wide camera detection."""
        result = get_dji_drone_name("FC8282")
        self.assertEqual(result, "DJI Air 3 Wide")

    def test_multi_camera_drones__air_3_tele__returns_correct_name(self):
        """Test Air 3 telephoto camera detection."""
        result = get_dji_drone_name("FC8284")
        self.assertEqual(result, "DJI Air 3 Tele")

    def test_interchangeable_cameras__x5s__returns_with_platform(self):
        """Test Zenmuse X5S returns with platform name."""
        result = get_dji_drone_name("FC6520")
        self.assertEqual(result, "DJI Inspire 2 + Zenmuse X5S")

    def test_interchangeable_cameras__x7__returns_with_platform(self):
        """Test Zenmuse X7 returns with platform name."""
        result = get_dji_drone_name("FC6540")
        self.assertEqual(result, "DJI Inspire 2 + Zenmuse X7")

    def test_interchangeable_cameras__x5__returns_with_platform(self):
        """Test Zenmuse X5 returns with platform name."""
        result = get_dji_drone_name("FC550")
        self.assertEqual(result, "DJI Inspire 1 + Zenmuse X5")

    def test_interchangeable_cameras__h20t__returns_with_platform(self):
        """Test Zenmuse H20T returns with platform name."""
        result = get_dji_drone_name("ZH20T")
        self.assertEqual(result, "DJI Matrice 300 + Zenmuse H20T")

    def test_integrated_enterprise__m3t__returns_correct_name(self):
        """Test Mavic 3 Thermal detection."""
        result = get_dji_drone_name("M3T")
        self.assertEqual(result, "DJI Mavic 3 Thermal")

    def test_integrated_enterprise__m30t__returns_correct_name(self):
        """Test Matrice 30T detection."""
        result = get_dji_drone_name("M30T")
        self.assertEqual(result, "DJI Matrice 30T")

    def test_unknown_fc_code__returns_none(self):
        """Test unknown FC code returns None."""
        result = get_dji_drone_name("FC9999")
        self.assertIsNone(result)

    def test_empty_string__returns_none(self):
        """Test empty string returns None."""
        result = get_dji_drone_name("")
        self.assertIsNone(result)

    def test_none_input__returns_none(self):
        """Test None input returns None."""
        result = get_dji_drone_name(None)
        self.assertIsNone(result)

    def test_get_dji_camera_info__mini_3_pro__returns_full_info(self):
        """Test detailed camera info for Mini 3 Pro."""
        result = get_dji_camera_info("FC3582")
        self.assertIsNotNone(result)
        name, camera_type, is_interchangeable = result
        self.assertEqual(name, "DJI Mini 3 Pro")
        self.assertEqual(camera_type, "single")
        self.assertFalse(is_interchangeable)

    def test_get_dji_camera_info__x5s__returns_interchangeable_info(self):
        """Test detailed camera info for Zenmuse X5S."""
        result = get_dji_camera_info("FC6520")
        self.assertIsNotNone(result)
        name, camera_type, is_interchangeable = result
        self.assertEqual(name, "DJI Inspire 2 + Zenmuse X5S")
        self.assertEqual(camera_type, "interchangeable")
        self.assertTrue(is_interchangeable)

    def test_get_dji_camera_info__air_3_wide__returns_multi_info(self):
        """Test detailed camera info for Air 3 wide camera."""
        result = get_dji_camera_info("FC8282")
        self.assertIsNotNone(result)
        name, camera_type, is_interchangeable = result
        self.assertEqual(name, "DJI Air 3 Wide")
        self.assertEqual(camera_type, "multi")
        self.assertFalse(is_interchangeable)

    def test_is_dji_camera__known_code__returns_true(self):
        """Test is_dji_camera returns True for known codes."""
        self.assertTrue(is_dji_camera("FC3582"))
        self.assertTrue(is_dji_camera("FC6520"))
        self.assertTrue(is_dji_camera("M3T"))

    def test_is_dji_camera__unknown_code__returns_false(self):
        """Test is_dji_camera returns False for unknown codes."""
        self.assertFalse(is_dji_camera("FC9999"))
        self.assertFalse(is_dji_camera(""))
        self.assertFalse(is_dji_camera(None))


if __name__ == "__main__":
    unittest.main()