"""
Unit tests for split_into_batches() function - Edge Cases

Tests the batch splitting logic with all edge cases including:
- Empty records
- Single record
- Below/at/above batch size limit
- Multiple batches
- Invalid batch sizes
- Large datasets
- Warning log verification

Author: Unit Test Specialist
Created: 2026-01-04
Related: PR #120 (Getty Images batch size 128 limit)
"""

import pytest
import logging
from typing import List, Dict
from createbatchlib.media_preparation import split_into_batches


# Fixtures

@pytest.fixture
def sample_record() -> Dict[str, str]:
    """Single sample record for testing."""
    return {
        "Cesta": "J:/Foto/JPG/Nature/2024/01/Camera/DSC00001.jpg",
        "Název": "Beautiful sunset",
        "Popis": "Sunset over mountains",
        "Klíčová slova": "sunset, nature, mountains"
    }


@pytest.fixture
def create_records(sample_record):
    """Factory fixture to create N records."""
    def _create(count: int) -> List[Dict[str, str]]:
        """Create count records with unique filenames."""
        return [
            {**sample_record, "Cesta": f"DSC{i:05d}.jpg"}
            for i in range(count)
        ]
    return _create


# Edge Case Tests

@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__empty_records_returns_empty_list():
    """Test that empty records list returns empty list."""
    result = split_into_batches([], batch_size=128)

    assert result == [], "Empty records should return empty list"
    assert isinstance(result, list), "Return type should be list"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__single_record_returns_single_batch(sample_record):
    """Test that single record returns one batch with one item."""
    records = [sample_record]
    result = split_into_batches(records, batch_size=128)

    assert len(result) == 1, "Should return 1 batch"
    assert len(result[0]) == 1, "Batch should contain 1 item"
    assert result[0][0] == sample_record, "Item should match original"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__below_limit_returns_single_batch(create_records):
    """Test that 127 items with batch_size=128 returns single batch."""
    records = create_records(127)
    result = split_into_batches(records, batch_size=128)

    assert len(result) == 1, "Should return 1 batch for 127 items"
    assert len(result[0]) == 127, "Batch should contain all 127 items"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__exact_limit_returns_single_batch(create_records):
    """Test that exactly 128 items with batch_size=128 returns single batch."""
    records = create_records(128)
    result = split_into_batches(records, batch_size=128)

    assert len(result) == 1, "Should return 1 batch for exactly 128 items"
    assert len(result[0]) == 128, "Batch should contain all 128 items"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__one_over_limit_returns_two_batches(create_records):
    """Test that 129 items with batch_size=128 returns two batches."""
    records = create_records(129)
    result = split_into_batches(records, batch_size=128)

    assert len(result) == 2, "Should return 2 batches for 129 items"
    assert len(result[0]) == 128, "First batch should have 128 items"
    assert len(result[1]) == 1, "Second batch should have 1 item"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__multiple_full_batches(create_records):
    """Test that 256 items with batch_size=128 returns two full batches."""
    records = create_records(256)
    result = split_into_batches(records, batch_size=128)

    assert len(result) == 2, "Should return 2 batches for 256 items"
    assert len(result[0]) == 128, "First batch should have 128 items"
    assert len(result[1]) == 128, "Second batch should have 128 items"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__invalid_batch_size_zero_returns_all(create_records):
    """Test that batch_size=0 returns all records in single batch."""
    records = create_records(50)
    result = split_into_batches(records, batch_size=0)

    assert len(result) == 1, "Should return 1 batch for invalid batch_size=0"
    assert len(result[0]) == 50, "Batch should contain all 50 items"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__invalid_batch_size_negative_returns_all(create_records):
    """Test that batch_size=-1 returns all records in single batch."""
    records = create_records(50)
    result = split_into_batches(records, batch_size=-1)

    assert len(result) == 1, "Should return 1 batch for invalid batch_size=-1"
    assert len(result[0]) == 50, "Batch should contain all 50 items"


@pytest.mark.timeout(30)
def test_media_preparation__split_into_batches__large_dataset_splits_correctly(create_records):
    """Test that 1000 items with batch_size=128 splits into correct batches."""
    records = create_records(1000)
    result = split_into_batches(records, batch_size=128)

    expected_batches = 8  # 1000 / 128 = 7.8125 → 8 batches
    assert len(result) == expected_batches, f"Should return {expected_batches} batches for 1000 items"

    # Verify batch sizes
    for i in range(7):
        assert len(result[i]) == 128, f"Batch {i} should have 128 items"

    # Last batch should have remainder
    assert len(result[7]) == 1000 - (7 * 128), "Last batch should have remainder items"

    # Verify total count
    total_items = sum(len(batch) for batch in result)
    assert total_items == 1000, "Total items should be 1000"


# Parametrized Tests

@pytest.mark.timeout(10)
@pytest.mark.parametrize("record_count,batch_size,expected_batches", [
    (0, 128, 0),      # Empty
    (1, 128, 1),      # Single
    (50, 128, 1),     # Below limit
    (127, 128, 1),    # One below limit
    (128, 128, 1),    # Exact limit
    (129, 128, 2),    # One over limit
    (256, 128, 2),    # Two full batches
    (257, 128, 3),    # Two full + partial
    (500, 128, 4),    # Multiple batches
    (1000, 100, 10),  # Different batch size
    (1001, 100, 11),  # Different batch size + remainder
])
def test_media_preparation__split_into_batches__parametrized_batch_counts(
    create_records, record_count, batch_size, expected_batches
):
    """Parametrized test for various record counts and batch sizes."""
    records = create_records(record_count)
    result = split_into_batches(records, batch_size)

    assert len(result) == expected_batches, (
        f"Expected {expected_batches} batches for {record_count} records "
        f"with batch_size={batch_size}, got {len(result)}"
    )


@pytest.mark.timeout(10)
@pytest.mark.parametrize("invalid_size", [0, -1, -10, -100])
def test_media_preparation__split_into_batches__invalid_sizes_return_single_batch(
    create_records, invalid_size
):
    """Test that various invalid batch sizes return single batch."""
    records = create_records(50)
    result = split_into_batches(records, batch_size=invalid_size)

    assert len(result) == 1, f"Invalid batch_size={invalid_size} should return 1 batch"
    assert len(result[0]) == 50, f"Batch should contain all items for invalid size {invalid_size}"


# Logging Tests

@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__empty_records_logs_warning(caplog):
    """Test that empty records triggers warning log."""
    with caplog.at_level(logging.WARNING):
        split_into_batches([], batch_size=128)

    assert "empty records list" in caplog.text.lower(), "Should log warning for empty records"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__invalid_batch_size_logs_warning(caplog, create_records):
    """Test that invalid batch_size triggers warning log."""
    records = create_records(10)

    with caplog.at_level(logging.WARNING):
        split_into_batches(records, batch_size=0)

    assert "invalid batch_size" in caplog.text.lower(), "Should log warning for invalid batch_size"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__valid_split_logs_info(caplog, create_records):
    """Test that valid split logs info message."""
    records = create_records(256)

    with caplog.at_level(logging.INFO):
        split_into_batches(records, batch_size=128)

    assert "split 256 records into 2 batches" in caplog.text.lower(), "Should log info for successful split"


# Data Integrity Tests

@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__preserves_record_order(create_records):
    """Test that record order is preserved across batches."""
    records = create_records(300)
    result = split_into_batches(records, batch_size=128)

    # Flatten batches back to single list
    flattened = []
    for batch in result:
        flattened.extend(batch)

    assert flattened == records, "Record order should be preserved"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__no_record_duplication(create_records):
    """Test that no records are duplicated in batches."""
    records = create_records(300)
    result = split_into_batches(records, batch_size=128)

    # Extract all filenames
    all_filenames = []
    for batch in result:
        for record in batch:
            all_filenames.append(record["Cesta"])

    # Check for duplicates
    assert len(all_filenames) == len(set(all_filenames)), "No records should be duplicated"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__no_record_loss(create_records):
    """Test that all records are included in batches."""
    records = create_records(300)
    result = split_into_batches(records, batch_size=128)

    total_items = sum(len(batch) for batch in result)
    assert total_items == 300, "All records should be included in batches"


# Boundary Tests

@pytest.mark.timeout(10)
@pytest.mark.parametrize("count", [127, 128, 129, 255, 256, 257])
def test_media_preparation__split_into_batches__boundary_values(create_records, count):
    """Test boundary values around batch_size=128."""
    records = create_records(count)
    result = split_into_batches(records, batch_size=128)

    # Verify total count
    total_items = sum(len(batch) for batch in result)
    assert total_items == count, f"Total items should be {count}"

    # Verify no batch exceeds limit
    for i, batch in enumerate(result):
        assert len(batch) <= 128, f"Batch {i} should not exceed 128 items"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])