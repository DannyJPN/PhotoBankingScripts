"""
Unit tests for createbatch optimization module.

Tests core functionality of RecordProcessor class including:
- Bank extraction from records
- Prepared status filtering
- Single-pass grouping logic
- Edge cases and error handling

Author: Claude Code
Date: 2025-11-29
"""

import pytest
from typing import Dict, List
from createbatchlib.optimization import RecordProcessor


class TestRecordProcessor:
    """Unit tests for RecordProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create a standard RecordProcessor instance."""
        return RecordProcessor("status", "připraveno")

    def test_extract_prepared_banks_single_bank(self, processor):
        """Test extracting bank name from single prepared status field."""
        record = {
            'Cesta': '/path/to/photo.jpg',
            'Shutterstock Status': 'připraveno',
            'Adobe Stock Status': 'nepřipraveno'
        }

        banks = processor._extract_prepared_banks(record)
        assert banks == ['Shutterstock']

    def test_extract_prepared_banks_multiple_banks(self, processor):
        """Test extracting multiple bank names from record."""
        record = {
            'Cesta': '/path/to/photo.jpg',
            'Shutterstock Status': 'připraveno',
            'Adobe Stock Status': 'připraveno',
            'Getty Images Status': 'nepřipraveno'
        }

        banks = processor._extract_prepared_banks(record)
        assert set(banks) == {'Shutterstock', 'AdobeStock'}

    def test_extract_prepared_banks_case_insensitive(self, processor):
        """Test that status matching is case-insensitive."""
        record = {
            'Cesta': '/path/to/photo.jpg',
            'Shutterstock STATUS': 'PŘIPRAVENO',
            'Adobe Stock status': 'Připraveno'
        }

        banks = processor._extract_prepared_banks(record)
        assert set(banks) == {'Shutterstock', 'AdobeStock'}

    def test_extract_prepared_banks_no_prepared(self, processor):
        """Test that no banks are extracted when none are prepared."""
        record = {
            'Cesta': '/path/to/photo.jpg',
            'Shutterstock Status': 'nepřipraveno',
            'Adobe Stock Status': 'nepřipraveno'
        }

        banks = processor._extract_prepared_banks(record)
        assert banks == []

    def test_extract_prepared_banks_empty_record(self, processor):
        """Test handling of empty record."""
        record = {}
        banks = processor._extract_prepared_banks(record)
        assert banks == []

    def test_extract_prepared_banks_non_string_values(self, processor):
        """Test handling of non-string status values."""
        record = {
            'Cesta': '/path/to/photo.jpg',
            'Shutterstock Status': 'připraveno',
            'Adobe Stock Status': None,  # Non-string value
            'Getty Images Status': 123   # Non-string value
        }

        banks = processor._extract_prepared_banks(record)
        assert banks == ['Shutterstock']

    def test_process_records_optimized_basic(self, processor):
        """Test basic single-pass processing."""
        records = [
            {'Cesta': '/photo1.jpg', 'Shutterstock Status': 'připraveno'},
            {'Cesta': '/photo2.jpg', 'Adobe Stock Status': 'připraveno'},
            {'Cesta': '/photo3.jpg', 'Shutterstock Status': 'nepřipraveno'},
        ]

        result = processor.process_records_optimized(records)

        assert 'Shutterstock' in result
        assert 'AdobeStock' in result
        assert len(result['Shutterstock']) == 1
        assert len(result['AdobeStock']) == 1

    def test_process_records_optimized_multiple_banks_per_record(self, processor):
        """Test record belonging to multiple banks."""
        records = [
            {
                'Cesta': '/photo1.jpg',
                'Shutterstock Status': 'připraveno',
                'Adobe Stock Status': 'připraveno'
            }
        ]

        result = processor.process_records_optimized(records)

        assert 'Shutterstock' in result
        assert 'AdobeStock' in result
        # Same record should appear in both banks
        assert len(result['Shutterstock']) == 1
        assert len(result['AdobeStock']) == 1
        assert result['Shutterstock'][0] is result['AdobeStock'][0]  # Same object

    def test_process_records_optimized_exclude_edited(self, processor):
        """Test exclusion of edited photos."""
        records = [
            {'Cesta': '/original/photo1.jpg', 'Shutterstock Status': 'připraveno'},
            {'Cesta': '/upravené/photo2.jpg', 'Shutterstock Status': 'připraveno'},
            {'Cesta': '/Upravené Foto/photo3.jpg', 'Adobe Stock Status': 'připraveno'},
        ]

        result = processor.process_records_optimized(records, include_edited=False)

        # Should only include the non-edited photo
        assert 'Shutterstock' in result
        assert len(result['Shutterstock']) == 1
        assert 'original' in result['Shutterstock'][0]['Cesta']

        # Edited photo for Adobe Stock should be excluded
        assert 'AdobeStock' not in result

    def test_process_records_optimized_include_edited(self, processor):
        """Test inclusion of edited photos when flag is set."""
        records = [
            {'Cesta': '/original/photo1.jpg', 'Shutterstock Status': 'připraveno'},
            {'Cesta': '/upravené/photo2.jpg', 'Shutterstock Status': 'připraveno'},
        ]

        result = processor.process_records_optimized(records, include_edited=True)

        assert 'Shutterstock' in result
        assert len(result['Shutterstock']) == 2

    def test_process_records_optimized_empty_list(self, processor):
        """Test processing empty record list."""
        result = processor.process_records_optimized([])
        assert result == {}

    def test_process_records_optimized_no_prepared_records(self, processor):
        """Test processing when no records are prepared."""
        records = [
            {'Cesta': '/photo1.jpg', 'Shutterstock Status': 'nepřipraveno'},
            {'Cesta': '/photo2.jpg', 'Adobe Stock Status': 'nepřipraveno'},
        ]

        result = processor.process_records_optimized(records)
        assert result == {}

    def test_get_bank_statistics(self, processor):
        """Test bank statistics generation."""
        bank_records_map = {
            'Shutterstock': [{'a': '1'}, {'b': '2'}, {'c': '3'}],
            'AdobeStock': [{'d': '4'}, {'e': '5'}],
            'GettyImages': [{'f': '6'}]
        }

        stats = processor.get_bank_statistics(bank_records_map)

        assert stats == {
            'Shutterstock': 3,
            'AdobeStock': 2,
            'GettyImages': 1
        }

    def test_get_bank_statistics_empty(self, processor):
        """Test statistics for empty result."""
        stats = processor.get_bank_statistics({})
        assert stats == {}

    def test_bank_name_extraction_with_spaces(self, processor):
        """Test correct extraction of bank names with multiple spaces."""
        record = {
            'Cesta': '/photo.jpg',
            'Getty Images   Status': 'připraveno',  # Multiple spaces
            '  Alamy  status  ': 'připraveno',      # Leading/trailing spaces
        }

        banks = processor._extract_prepared_banks(record)
        # Should strip whitespace correctly
        assert 'GettyImages' in banks
        # Note: Leading spaces in column name would be unusual but should handle

    def test_sorted_bank_order(self, processor):
        """Test that banks are returned in sorted order."""
        records = [
            {'Cesta': '/photo1.jpg', 'Shutterstock Status': 'připraveno'},
            {'Cesta': '/photo2.jpg', 'Adobe Stock Status': 'připraveno'},
            {'Cesta': '/photo3.jpg', 'Getty Images Status': 'připraveno'},
        ]

        result = processor.process_records_optimized(records)
        bank_names = list(result.keys())

        # Should be alphabetically sorted
        assert bank_names == sorted(bank_names)

    def test_custom_status_keyword(self):
        """Test processor with custom status keyword."""
        processor = RecordProcessor("stav", "hotovo")
        record = {
            'Cesta': '/photo.jpg',
            'Shutterstock Stav': 'hotovo',
            'Adobe Stock Status': 'připraveno'  # Different keyword, should be ignored
        }

        banks = processor._extract_prepared_banks(record)
        assert banks == ['Shutterstock']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
