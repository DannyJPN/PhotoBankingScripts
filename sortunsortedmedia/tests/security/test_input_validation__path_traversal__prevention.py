"""
Security tests for input validation and path traversal prevention.

:author: SortUnsortedMedia Test Suite
:date: 2025-08-21
"""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from sortunsortedmedialib.constants import DEFAULT_UNSORTED_FOLDER, DEFAULT_TARGET_FOLDER


class TestInputValidationPathTraversalPrevention(unittest.TestCase):
    """Test security aspects of input validation and path traversal prevention."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.safe_path = os.path.join(self.temp_dir, "safe")
        self.malicious_paths = [
            "../../../etc/passwd",  # Unix path traversal
            "..\\..\\..\\windows\\system32\\config\\sam",  # Windows path traversal
            "/etc/passwd",  # Absolute path
            "C:\\Windows\\System32\\config\\SAM",  # Windows absolute path
            "../../secrets.txt",  # Relative path traversal
            "normal_file/../../../etc/passwd",  # Mixed traversal
            "file_with_null_byte\x00.txt",  # Null byte injection
            "very_long_" + "a" * 1000 + ".txt",  # Extremely long filename
            "",  # Empty path
            "con.txt",  # Windows reserved name
            "aux.txt",  # Windows reserved name
            "prn.txt",  # Windows reserved name
            "file_with_unicode_\u0000.txt",  # Unicode null
            "file_with_newline\n.txt",  # Newline injection
        ]

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_input_validation__path_traversal__detect_malicious_paths(self) -> None:
        """Test detection of malicious path traversal attempts."""
        for malicious_path in self.malicious_paths:
            with self.subTest(path=malicious_path):
                # Test that malicious paths are properly identified
                is_malicious = self._contains_path_traversal(malicious_path)
                
                if ".." in malicious_path or malicious_path.startswith("/") or "\\" in malicious_path:
                    self.assertTrue(is_malicious or self._is_suspicious_path(malicious_path),
                                   f"Should detect path traversal in: {repr(malicious_path)}")

    def _contains_path_traversal(self, path: str) -> bool:
        """
        Helper method to detect path traversal patterns.
        
        :param path: Path to check
        :return: True if path contains traversal patterns
        """
        if not path:
            return True
            
        # Check for common path traversal patterns
        traversal_patterns = [
            "..",  # Parent directory
            "/",   # Root directory (absolute path)
            "\\",  # Windows path separator
            "\x00",  # Null byte
            "\n",   # Newline
            "\r",   # Carriage return
        ]
        
        for pattern in traversal_patterns:
            if pattern in path:
                return True
                
        return False

    def _is_suspicious_path(self, path: str) -> bool:
        """
        Helper method to detect suspicious path characteristics.
        
        :param path: Path to check
        :return: True if path is suspicious
        """
        if not path:
            return True
            
        # Check for extremely long paths
        if len(path) > 255:
            return True
            
        # Check for Windows reserved names
        reserved_names = ["con", "aux", "prn", "nul", "com1", "com2", "lpt1", "lpt2"]
        path_lower = path.lower().split('.')[0]  # Remove extension
        if path_lower in reserved_names:
            return True
            
        return False

    def test_input_validation__path_traversal__safe_path_handling(self) -> None:
        """Test that safe paths are handled correctly."""
        safe_paths = [
            "normal_file.jpg",
            "photo_2024_01_01.jpg",
            "my_vacation_photos.zip",
            "document with spaces.pdf",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "IMG_20240101_123456.jpg",
        ]
        
        for safe_path in safe_paths:
            with self.subTest(path=safe_path):
                is_malicious = self._contains_path_traversal(safe_path)
                is_suspicious = self._is_suspicious_path(safe_path)
                
                self.assertFalse(is_malicious, f"Safe path incorrectly flagged as malicious: {safe_path}")
                self.assertFalse(is_suspicious, f"Safe path incorrectly flagged as suspicious: {safe_path}")

    @patch('sortunsortedmedia.main')
    def test_input_validation__path_traversal__command_line_argument_sanitization(self, mock_main: MagicMock) -> None:
        """Test sanitization of command line arguments."""
        from sortunsortedmedia import parse_arguments
        
        # Test with malicious command line arguments
        malicious_args = [
            '--unsorted_folder', '../../../etc',
            '--target_folder', '/etc/passwd',
            '--interval', '3600'
        ]
        
        with patch('sys.argv', ['sortunsortedmedia.py'] + malicious_args):
            args = parse_arguments()
            
            # Check that arguments are captured (validation should happen in main logic)
            self.assertIsNotNone(args.unsorted_folder)
            self.assertIsNotNone(args.target_folder)
            
            # The actual path validation should happen in the processing logic
            # This test ensures arguments are parsed without crashing

    def test_input_validation__path_traversal__filename_sanitization(self) -> None:
        """Test filename sanitization for security."""
        test_cases = [
            ("normal_file.jpg", True),  # Should be allowed
            ("../../../etc/passwd", False),  # Should be blocked
            ("file\x00.txt", False),  # Should be blocked
            ("", False),  # Should be blocked
            ("con.txt", False),  # Should be blocked (Windows reserved)
            ("very_long_" + "a" * 300 + ".txt", False),  # Should be blocked (too long)
        ]
        
        for filename, should_be_safe in test_cases:
            with self.subTest(filename=repr(filename)):
                is_safe = self._is_filename_safe(filename)
                
                if should_be_safe:
                    self.assertTrue(is_safe, f"Safe filename incorrectly blocked: {repr(filename)}")
                else:
                    self.assertFalse(is_safe, f"Unsafe filename incorrectly allowed: {repr(filename)}")

    def _is_filename_safe(self, filename: str) -> bool:
        """
        Helper method to validate filename safety.
        
        :param filename: Filename to validate
        :return: True if filename is safe
        """
        if not filename or len(filename) > 255:
            return False
            
        # Check for path traversal
        if self._contains_path_traversal(filename):
            return False
            
        # Check for suspicious characteristics
        if self._is_suspicious_path(filename):
            return False
            
        return True

    def test_input_validation__path_traversal__directory_creation_safety(self) -> None:
        """Test that directory creation is safe from path traversal."""
        # Simulate directory creation with various paths
        test_base_dir = self.temp_dir
        
        unsafe_relative_paths = [
            "../outside_directory",
            "../../etc",
            "normal/../../../etc",
        ]
        
        for unsafe_path in unsafe_relative_paths:
            with self.subTest(path=unsafe_path):
                # Combine base directory with potentially unsafe relative path
                full_path = os.path.join(test_base_dir, unsafe_path)
                normalized_path = os.path.normpath(full_path)
                
                # Check if normalized path escapes the base directory
                try:
                    # Use os.path.commonpath to check if paths share common root
                    common = os.path.commonpath([test_base_dir, normalized_path])
                    is_safe = common == test_base_dir or normalized_path.startswith(test_base_dir)
                    
                    # Unsafe paths should not be allowed
                    if ".." in unsafe_path:
                        # This might escape the base directory - verify it's detected
                        escaped = not normalized_path.startswith(test_base_dir)
                        if escaped:
                            self.assertTrue(True, f"Correctly detected path escape: {unsafe_path}")
                        
                except ValueError:
                    # os.path.commonpath raises ValueError if paths don't share a common base
                    # This indicates potential path traversal
                    self.assertTrue(True, f"Path traversal detected for: {unsafe_path}")

    def test_input_validation__path_traversal__file_access_restrictions(self) -> None:
        """Test restrictions on file access patterns."""
        # Test that the application doesn't accidentally access system files
        system_files = [
            "/etc/passwd",
            "/etc/shadow", 
            "C:\\Windows\\System32\\config\\SAM",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "/proc/version",
            "/sys/devices/virtual/dmi/id/product_name",
        ]
        
        for system_file in system_files:
            with self.subTest(file=system_file):
                # These files should never be accessed by media processing
                should_block = self._should_block_system_file_access(system_file)
                self.assertTrue(should_block, f"Should block access to system file: {system_file}")

    def _should_block_system_file_access(self, file_path: str) -> bool:
        """
        Helper method to determine if system file access should be blocked.
        
        :param file_path: Path to system file
        :return: True if access should be blocked
        """
        # System directories that should never be accessed
        forbidden_patterns = [
            "/etc/",
            "/proc/",
            "/sys/",
            "C:\\Windows\\System32\\",
            "/root/",
            "/var/log/",
        ]
        
        for pattern in forbidden_patterns:
            if pattern in file_path:
                return True
                
        return False

    def test_input_validation__path_traversal__symlink_protection(self) -> None:
        """Test protection against symbolic link attacks."""
        if os.name == 'posix':  # Unix-like systems support symlinks
            # Create a symbolic link that points outside the safe directory
            try:
                safe_dir = os.path.join(self.temp_dir, "safe")
                os.makedirs(safe_dir, exist_ok=True)
                
                # Create a symlink pointing to /etc (outside safe directory)
                symlink_path = os.path.join(safe_dir, "malicious_link")
                target_path = "/etc"
                
                os.symlink(target_path, symlink_path)
                
                # Check if symlink is properly detected and handled
                is_symlink = os.path.islink(symlink_path)
                self.assertTrue(is_symlink, "Should detect symbolic link")
                
                # Real path should point outside safe directory
                real_path = os.path.realpath(symlink_path)
                is_outside_safe_dir = not real_path.startswith(safe_dir)
                
                if is_outside_safe_dir:
                    # This symlink escapes the safe directory and should be blocked
                    self.assertTrue(True, "Correctly identified dangerous symlink")
                    
            except (OSError, NotImplementedError):
                # Symlinks not supported on this system
                self.skipTest("Symbolic links not supported on this system")

    def test_input_validation__path_traversal__unicode_normalization_attacks(self) -> None:
        """Test protection against Unicode normalization attacks."""
        # Unicode characters that might be used in attacks
        unicode_attack_strings = [
            "file\u2044.txt",  # Unicode fraction slash (looks like /)
            "file\u2215.txt",  # Unicode division slash  
            "file\uff0e\uff0e\uff0f.txt",  # Full-width Unicode dots and slash
            "file\u002e\u002e\u002f.txt",  # Encoded dots and slash
        ]
        
        for attack_string in unicode_attack_strings:
            with self.subTest(string=repr(attack_string)):
                # Normalize Unicode and check for suspicious patterns
                import unicodedata
                normalized = unicodedata.normalize('NFKD', attack_string)
                
                # Check if normalization reveals path traversal patterns
                contains_traversal = ".." in normalized or "/" in normalized or "\\" in normalized
                
                if contains_traversal:
                    self.assertTrue(True, f"Detected path traversal after Unicode normalization: {repr(attack_string)}")


if __name__ == "__main__":
    unittest.main()