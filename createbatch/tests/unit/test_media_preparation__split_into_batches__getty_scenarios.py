"""
Unit tests for split_into_batches() function - Getty Images Scenarios

Tests specific Getty Images use cases with 128-item batch limit:
- Real PhotoMedia.csv record structures
- Getty-specific batch sizes
- Integration with PHOTOBANK_BATCH_SIZE_LIMITS constant

Author: Unit Test Specialist
Created: 2026-01-04
Related: PR #120 (Getty Images batch size 128 limit)
"""

import pytest
from typing import List, Dict
from createbatchlib.media_preparation import split_into_batches
from createbatchlib.constants import PHOTOBANK_BATCH_SIZE_LIMITS


# Fixtures

@pytest.fixture
def getty_batch_limit() -> int:
    """Getty Images batch size limit from constants."""
    return PHOTOBANK_BATCH_SIZE_LIMITS.get('Getty Images', 128)


@pytest.fixture
def photomedia_record() -> Dict[str, str]:
    """Sample PhotoMedia.csv record structure."""
    return {
        "Cesta": "J:/Foto/JPG/Nature/2024/01/Camera/DSC00001.jpg",
        "Název": "Mountain landscape",
        "Popis": "Beautiful mountain landscape at sunset",
        "Klíčová slova": "mountain, landscape, sunset, nature",
        "Datum pořízení": "2024-01-15 14:30:00",
        "Getty Images status": "připraveno",
        "Getty Images category": "Nature",
        "Shutterstock status": "připraveno",
        "Adobe Stock status": "připraveno"
    }


@pytest.fixture
def create_photomedia_records(photomedia_record):
    """Factory to create N PhotoMedia.csv records."""
    def _create(count: int) -> List[Dict[str, str]]:
        return [
            {
                **photomedia_record,
                "Cesta": f"J:/Foto/JPG/Nature/2024/01/Camera/DSC{i:05d}.jpg",
                "Název": f"Photo {i}",
            }
            for i in range(1, count + 1)
        ]
    return _create


# Getty Specific Tests

@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__getty_limit_constant_is_128(getty_batch_limit):
    """Verify Getty Images batch limit is set to 128 in constants."""
    assert getty_batch_limit == 128, "Getty Images batch limit should be 128"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__getty_exact_limit(
    create_photomedia_records, getty_batch_limit
):
    """Test Getty with exactly 128 items creates single batch."""
    records = create_photomedia_records(128)
    result = split_into_batches(records, batch_size=getty_batch_limit)

    assert len(result) == 1, "128 Getty items should create 1 batch"
    assert len(result[0]) == 128, "Batch should contain all 128 items"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__getty_one_over_limit(
    create_photomedia_records, getty_batch_limit
):
    """Test Getty with 129 items creates two batches (128 + 1)."""
    records = create_photomedia_records(129)
    result = split_into_batches(records, batch_size=getty_batch_limit)

    assert len(result) == 2, "129 Getty items should create 2 batches"
    assert len(result[0]) == 128, "First batch should have 128 items"
    assert len(result[1]) == 1, "Second batch should have 1 item"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__getty_typical_small_batch(
    create_photomedia_records, getty_batch_limit
):
    """Test Getty with typical small batch (50 items)."""
    records = create_photomedia_records(50)
    result = split_into_batches(records, batch_size=getty_batch_limit)

    assert len(result) == 1, "50 Getty items should create 1 batch"
    assert len(result[0]) == 50, "Batch should contain all 50 items"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__getty_typical_large_batch(
    create_photomedia_records, getty_batch_limit
):
    """Test Getty with typical large batch (300 items)."""
    records = create_photomedia_records(300)
    result = split_into_batches(records, batch_size=getty_batch_limit)

    expected_batches = 3  # 300 / 128 = 2.34 → 3 batches
    assert len(result) == expected_batches, f"300 Getty items should create {expected_batches} batches"
    assert len(result[0]) == 128, "First batch should have 128 items"
    assert len(result[1]) == 128, "Second batch should have 128 items"
    assert len(result[2]) == 44, "Third batch should have 44 items (remainder)"


# Real-World Scenarios

@pytest.mark.timeout(10)
@pytest.mark.parametrize("item_count,expected_batches,expected_last_batch", [
    (1, 1, 1),        # Single photo
    (10, 1, 10),      # Small batch
    (50, 1, 50),      # Typical batch
    (100, 1, 100),    # Large single batch
    (127, 1, 127),    # Just under limit
    (128, 1, 128),    # Exact limit
    (129, 2, 1),      # One over
    (200, 2, 72),     # Two batches with remainder
    (256, 2, 128),    # Two full batches
    (300, 3, 44),     # Three batches with remainder
    (384, 3, 128),    # Three full batches
    (500, 4, 116),    # Four batches with remainder
    (1000, 8, 104),   # Large dataset
])
def test_media_preparation__split_into_batches__getty_real_world_scenarios(
    create_photomedia_records, getty_batch_limit,
    item_count, expected_batches, expected_last_batch
):
    """Test Getty batch splitting with real-world item counts."""
    records = create_photomedia_records(item_count)
    result = split_into_batches(records, batch_size=getty_batch_limit)

    assert len(result) == expected_batches, (
        f"Expected {expected_batches} batches for {item_count} Getty items"
    )

    # Verify last batch size
    assert len(result[-1]) == expected_last_batch, (
        f"Last batch should have {expected_last_batch} items"
    )

    # Verify all batches except last are full
    for i in range(len(result) - 1):
        assert len(result[i]) == getty_batch_limit, (
            f"Batch {i} should have {getty_batch_limit} items"
        )


# PhotoMedia.csv Field Preservation Tests

@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__preserves_photomedia_fields(
    create_photomedia_records, getty_batch_limit
):
    """Test that all PhotoMedia.csv fields are preserved in batches."""
    records = create_photomedia_records(150)
    result = split_into_batches(records, batch_size=getty_batch_limit)

    # Check first record in first batch
    first_record = result[0][0]
    required_fields = [
        "Cesta", "Název", "Popis", "Klíčová slova", "Datum pořízení",
        "Getty Images status", "Getty Images category",
        "Shutterstock status", "Adobe Stock status"
    ]

    for field in required_fields:
        assert field in first_record, f"Field '{field}' should be preserved"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__photomedia_record_integrity(
    create_photomedia_records, getty_batch_limit
):
    """Test that PhotoMedia.csv records maintain integrity across batches."""
    records = create_photomedia_records(200)
    original_paths = [r["Cesta"] for r in records]

    result = split_into_batches(records, batch_size=getty_batch_limit)

    # Flatten and extract paths
    flattened_paths = []
    for batch in result:
        for record in batch:
            flattened_paths.append(record["Cesta"])

    assert flattened_paths == original_paths, "Record paths should maintain order"
    assert len(flattened_paths) == len(set(flattened_paths)), "No duplicate records"


# Performance Expectations

@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__getty_max_single_batch_completes_quickly(
    create_photomedia_records, getty_batch_limit
):
    """Test that splitting 128 Getty items completes quickly."""
    records = create_photomedia_records(128)

    import time
    start = time.time()
    result = split_into_batches(records, batch_size=getty_batch_limit)
    duration = time.time() - start

    assert duration < 1.0, "Splitting 128 items should take < 1 second"
    assert len(result) == 1, "Should create 1 batch"


@pytest.mark.timeout(30)
def test_media_preparation__split_into_batches__getty_large_dataset_completes_quickly(
    create_photomedia_records, getty_batch_limit
):
    """Test that splitting 1000 Getty items completes quickly."""
    records = create_photomedia_records(1000)

    import time
    start = time.time()
    result = split_into_batches(records, batch_size=getty_batch_limit)
    duration = time.time() - start

    assert duration < 2.0, "Splitting 1000 items should take < 2 seconds"
    assert len(result) == 8, "Should create 8 batches"


# Edge Cases with Getty Limit

@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__getty_empty_records_safe(getty_batch_limit):
    """Test that empty Getty records list is handled safely."""
    result = split_into_batches([], batch_size=getty_batch_limit)

    assert result == [], "Empty Getty records should return empty list"


@pytest.mark.timeout(10)
def test_media_preparation__split_into_batches__getty_single_photo(
    photomedia_record, getty_batch_limit
):
    """Test that single Getty photo creates single batch."""
    records = [photomedia_record]
    result = split_into_batches(records, batch_size=getty_batch_limit)

    assert len(result) == 1, "Single Getty photo should create 1 batch"
    assert len(result[0]) == 1, "Batch should contain 1 item"
    assert result[0][0]["Getty Images status"] == "připraveno"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])