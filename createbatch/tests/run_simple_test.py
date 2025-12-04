#!/usr/bin/env python
"""
Simple standalone test for optimization verification.

This script runs basic tests without requiring pytest installation.
It verifies that the optimization works correctly and provides performance metrics.

Author: Claude Code
Date: 2025-11-29
"""

import sys
import os
import time
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from createbatchlib.optimization import RecordProcessor, compare_with_legacy_approach
from createbatchlib.constants import STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE


def generate_test_records(num_records=1000, num_banks=5):
    """Generate test records for validation."""
    banks = [f"Bank{i}" for i in range(1, num_banks + 1)]
    records = []

    for i in range(num_records):
        record = {
            'Cesta': f'/path/to/photo_{i}.jpg',
            'Název souboru': f'photo_{i}.jpg',
        }

        # Add status fields - 30% are prepared
        for bank in banks:
            if i < num_records * 0.3 and hash(f"{i}_{bank}") % 3 == 0:
                record[f'{bank} {STATUS_FIELD_KEYWORD}'] = PREPARED_STATUS_VALUE
            else:
                record[f'{bank} {STATUS_FIELD_KEYWORD}'] = 'nepřipraveno'

        records.append(record)

    return records


def test_basic_functionality():
    """Test basic RecordProcessor functionality."""
    print("\n=== Testing Basic Functionality ===")

    processor = RecordProcessor(STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE)

    # Test 1: Extract banks from single record
    record = {
        'Cesta': '/photo.jpg',
        'Shutterstock Status': 'připraveno',
        'Adobe Stock Status': 'připraveno',
        'Getty Images Status': 'nepřipraveno'
    }

    banks = processor._extract_prepared_banks(record)
    assert set(banks) == {'Shutterstock', 'Adobe Stock'}, f"Expected 2 banks, got: {banks}"
    print("✓ Bank extraction works correctly")

    # Test 2: Process multiple records
    records = [
        {'Cesta': '/photo1.jpg', 'Shutterstock Status': 'připraveno'},
        {'Cesta': '/photo2.jpg', 'Adobe Stock Status': 'připraveno'},
        {'Cesta': '/photo3.jpg', 'Shutterstock Status': 'nepřipraveno'},
    ]

    result = processor.process_records_optimized(records)
    assert 'Shutterstock' in result, "Shutterstock should be in results"
    assert 'Adobe Stock' in result, "Adobe Stock should be in results"
    assert len(result['Shutterstock']) == 1, "Shutterstock should have 1 record"
    print("✓ Record processing works correctly")

    # Test 3: Edited photos filtering
    records_with_edited = [
        {'Cesta': '/original/photo1.jpg', 'Shutterstock Status': 'připraveno'},
        {'Cesta': '/upravené/photo2.jpg', 'Shutterstock Status': 'připraveno'},
    ]

    result_no_edited = processor.process_records_optimized(records_with_edited, include_edited=False)
    assert len(result_no_edited['Shutterstock']) == 1, "Should exclude edited photo"

    result_with_edited = processor.process_records_optimized(records_with_edited, include_edited=True)
    assert len(result_with_edited['Shutterstock']) == 2, "Should include edited photo"
    print("✓ Edited photo filtering works correctly")

    print("\n✅ All basic functionality tests passed!")


def test_functional_equivalence():
    """Verify optimized approach produces same results as legacy."""
    print("\n=== Testing Functional Equivalence ===")

    records = generate_test_records(1000, num_banks=5)

    print(f"Testing with {len(records)} records...")

    optimized_results, legacy_results = compare_with_legacy_approach(
        records, STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE, include_edited=False
    )

    # Verify same banks
    opt_banks = set(optimized_results.keys())
    leg_banks = set(legacy_results.keys())
    assert opt_banks == leg_banks, f"Banks don't match: {opt_banks} vs {leg_banks}"
    print(f"✓ Both approaches found same {len(opt_banks)} banks")

    # Verify same record counts
    for bank in opt_banks:
        opt_count = len(optimized_results[bank])
        leg_count = len(legacy_results[bank])
        assert opt_count == leg_count, f"Bank {bank}: count mismatch {opt_count} vs {leg_count}"
        print(f"  ✓ {bank}: {opt_count} records")

    print("\n✅ Functional equivalence verified!")


def test_performance():
    """Test performance improvements."""
    print("\n=== Testing Performance ===")

    test_sizes = [1000, 5000, 10000]

    for size in test_sizes:
        print(f"\nTesting with {size} records...")
        records = generate_test_records(size, num_banks=10)

        # Measure optimized approach
        processor = RecordProcessor(STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE)
        start_time = time.time()
        result = processor.process_records_optimized(records)
        optimized_time = time.time() - start_time

        print(f"  Optimized: {optimized_time:.3f}s")
        print(f"  Found {len(result)} banks")

        total_records = sum(len(recs) for recs in result.values())
        print(f"  Processed {total_records} prepared records")

        # Performance should be reasonable
        assert optimized_time < 30.0, f"Performance too slow: {optimized_time}s"

    print("\n✅ Performance tests passed!")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n=== Testing Edge Cases ===")

    processor = RecordProcessor(STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE)

    # Empty list
    result = processor.process_records_optimized([])
    assert result == {}, "Empty list should return empty dict"
    print("✓ Empty list handled correctly")

    # No prepared records
    records = [
        {'Cesta': '/photo1.jpg', 'Shutterstock Status': 'nepřipraveno'},
    ]
    result = processor.process_records_optimized(records)
    assert result == {}, "No prepared records should return empty dict"
    print("✓ No prepared records handled correctly")

    # Non-string status values
    records = [
        {'Cesta': '/photo1.jpg', 'Shutterstock Status': 'připraveno'},
        {'Cesta': '/photo2.jpg', 'Adobe Stock Status': None},
        {'Cesta': '/photo3.jpg', 'Getty Images Status': 123},
    ]
    result = processor.process_records_optimized(records)
    assert 'Shutterstock' in result, "Should find valid status"
    assert len(result) == 1, "Should ignore non-string values"
    print("✓ Non-string values handled correctly")

    # Case insensitive matching
    records = [
        {'Cesta': '/photo1.jpg', 'Shutterstock STATUS': 'PŘIPRAVENO'},
    ]
    result = processor.process_records_optimized(records)
    assert 'Shutterstock' in result, "Should be case-insensitive"
    print("✓ Case-insensitive matching works")

    print("\n✅ All edge case tests passed!")


def main():
    """Run all tests."""
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise during testing
        format='%(levelname)s: %(message)s'
    )

    print("=" * 60)
    print("CreateBatch Optimization Test Suite")
    print("=" * 60)

    try:
        test_basic_functionality()
        test_edge_cases()
        test_functional_equivalence()
        test_performance()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
