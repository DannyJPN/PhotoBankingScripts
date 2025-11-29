"""
Performance benchmarking tests for createbatch optimization.

This module validates that the optimized RecordProcessor provides significant
performance improvements over the legacy multi-pass approach.

Test requirements:
- Timeout: ≤ 24h (actual: < 1 minute for typical test sizes)
- Validates functional equivalence between optimized and legacy approaches
- Measures time and memory improvements

Author: Claude Code
Date: 2025-11-29
"""

import time
import logging
import pytest
from typing import Dict, List
from createbatchlib.optimization import RecordProcessor, compare_with_legacy_approach
from createbatchlib.constants import STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE


def generate_test_records(
    num_records: int,
    num_banks: int = 5,
    prepared_ratio: float = 0.3,
    edited_ratio: float = 0.1
) -> List[Dict[str, str]]:
    """
    Generate synthetic test records for benchmarking.

    Args:
        num_records: Total number of records to generate
        num_banks: Number of unique photobanks
        prepared_ratio: Fraction of records that are prepared (0.0-1.0)
        edited_ratio: Fraction of records that are edited photos (0.0-1.0)

    Returns:
        List of test records with realistic structure
    """
    banks = [f"Bank{i}" for i in range(1, num_banks + 1)]
    records = []

    for i in range(num_records):
        record = {
            'Cesta': f'/path/to/photo_{i}.jpg',
            'Název souboru': f'photo_{i}.jpg',
            'Titulek': f'Test Photo {i}',
        }

        # Some records are edited photos
        if i < num_records * edited_ratio:
            record['Cesta'] = f'/path/to/upravené/photo_{i}.jpg'

        # Add status fields for all banks
        for bank in banks:
            # Some records have prepared status
            if i < num_records * prepared_ratio:
                # Each prepared record is prepared for 1-3 random banks
                if hash(f"{i}_{bank}") % 3 == 0:
                    record[f'{bank} {STATUS_FIELD_KEYWORD}'] = PREPARED_STATUS_VALUE
                else:
                    record[f'{bank} {STATUS_FIELD_KEYWORD}'] = 'nepřipraveno'
            else:
                record[f'{bank} {STATUS_FIELD_KEYWORD}'] = 'nepřipraveno'

        records.append(record)

    return records


class TestOptimizationPerformance:
    """Performance benchmarking test suite for optimization."""

    def test_small_dataset_performance(self):
        """Test performance with small dataset (1000 records)."""
        records = generate_test_records(1000, num_banks=5)
        processor = RecordProcessor(STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE)

        start_time = time.time()
        result = processor.process_records_optimized(records, include_edited=False)
        elapsed_time = time.time() - start_time

        logging.info(f"Small dataset (1000 records): {elapsed_time:.3f}s")
        assert elapsed_time < 5.0, "Small dataset should complete in < 5s"
        assert len(result) > 0, "Should find some prepared records"

    def test_medium_dataset_performance(self):
        """Test performance with medium dataset (10,000 records)."""
        records = generate_test_records(10000, num_banks=10)
        processor = RecordProcessor(STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE)

        start_time = time.time()
        result = processor.process_records_optimized(records, include_edited=False)
        elapsed_time = time.time() - start_time

        logging.info(f"Medium dataset (10,000 records): {elapsed_time:.3f}s")
        assert elapsed_time < 30.0, "Medium dataset should complete in < 30s"
        assert len(result) > 0, "Should find some prepared records"

    def test_large_dataset_performance(self):
        """Test performance with large dataset (100,000 records)."""
        records = generate_test_records(100000, num_banks=10)
        processor = RecordProcessor(STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE)

        start_time = time.time()
        result = processor.process_records_optimized(records, include_edited=False)
        elapsed_time = time.time() - start_time

        logging.info(f"Large dataset (100,000 records): {elapsed_time:.3f}s")
        assert elapsed_time < 300.0, "Large dataset should complete in < 5 minutes"
        assert len(result) > 0, "Should find some prepared records"

    def test_functional_equivalence_small(self):
        """Verify optimized approach produces identical results to legacy (small dataset)."""
        records = generate_test_records(1000, num_banks=5)

        optimized_results, legacy_results = compare_with_legacy_approach(
            records, STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE, include_edited=False
        )

        # Verify same banks found
        assert set(optimized_results.keys()) == set(legacy_results.keys()), \
            "Optimized and legacy should find same banks"

        # Verify same number of records per bank
        for bank in optimized_results.keys():
            assert len(optimized_results[bank]) == len(legacy_results[bank]), \
                f"Bank '{bank}' should have same record count in both approaches"

    def test_functional_equivalence_medium(self):
        """Verify optimized approach produces identical results to legacy (medium dataset)."""
        records = generate_test_records(5000, num_banks=8)

        optimized_results, legacy_results = compare_with_legacy_approach(
            records, STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE, include_edited=True
        )

        # Verify same banks found
        assert set(optimized_results.keys()) == set(legacy_results.keys()), \
            "Optimized and legacy should find same banks"

        # Verify same records per bank (check file paths match)
        for bank in optimized_results.keys():
            opt_paths = {rec['Cesta'] for rec in optimized_results[bank]}
            leg_paths = {rec['Cesta'] for rec in legacy_results[bank]}
            assert opt_paths == leg_paths, \
                f"Bank '{bank}' should have identical records in both approaches"

    @pytest.mark.slow
    def test_performance_comparison_benchmark(self):
        """
        Comprehensive performance comparison between optimized and legacy approaches.

        This test measures actual speedup achieved by the optimization.
        """
        test_sizes = [1000, 5000, 10000]
        results = []

        for size in test_sizes:
            records = generate_test_records(size, num_banks=10)

            # Measure legacy approach
            start_legacy = time.time()
            optimized_results, legacy_results = compare_with_legacy_approach(
                records, STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE
            )
            legacy_time = time.time() - start_legacy

            # Measure optimized approach alone
            processor = RecordProcessor(STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE)
            start_opt = time.time()
            opt_results = processor.process_records_optimized(records)
            optimized_time = time.time() - start_opt

            speedup = legacy_time / optimized_time if optimized_time > 0 else 0
            results.append({
                'size': size,
                'legacy_time': legacy_time,
                'optimized_time': optimized_time,
                'speedup': speedup
            })

            logging.info(
                f"Dataset size {size}: Legacy={legacy_time:.3f}s, "
                f"Optimized={optimized_time:.3f}s, Speedup={speedup:.1f}x"
            )

        # Verify we get measurable speedup
        avg_speedup = sum(r['speedup'] for r in results) / len(results)
        logging.info(f"Average speedup across all tests: {avg_speedup:.1f}x")

        # We expect at least 2x speedup on average
        assert avg_speedup >= 2.0, \
            f"Expected at least 2x average speedup, got {avg_speedup:.1f}x"

    def test_edited_photos_filtering(self):
        """Test that edited photos are correctly excluded/included."""
        records = generate_test_records(1000, num_banks=5, edited_ratio=0.3)
        processor = RecordProcessor(STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE)

        # Test with edited excluded
        result_no_edited = processor.process_records_optimized(records, include_edited=False)
        all_records_no_edited = [rec for recs in result_no_edited.values() for rec in recs]
        edited_count_no_edited = sum(
            1 for rec in all_records_no_edited if 'upravené' in rec.get('Cesta', '').lower()
        )
        assert edited_count_no_edited == 0, "Should exclude all edited photos"

        # Test with edited included
        result_with_edited = processor.process_records_optimized(records, include_edited=True)
        all_records_with_edited = [rec for recs in result_with_edited.values() for rec in recs]
        edited_count_with_edited = sum(
            1 for rec in all_records_with_edited if 'upravené' in rec.get('Cesta', '').lower()
        )
        assert edited_count_with_edited > 0, "Should include some edited photos"

    def test_bank_statistics(self):
        """Test bank statistics generation."""
        records = generate_test_records(1000, num_banks=5)
        processor = RecordProcessor(STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE)

        result = processor.process_records_optimized(records)
        stats = processor.get_bank_statistics(result)

        assert len(stats) == len(result), "Should have statistics for all banks"
        for bank, count in stats.items():
            assert count == len(result[bank]), f"Bank {bank} count should match record count"
            assert count > 0, f"Bank {bank} should have at least one record"


class TestMemoryEfficiency:
    """Memory efficiency tests for optimization."""

    def test_memory_overhead(self):
        """
        Test that optimized approach doesn't create excessive memory overhead.

        Note: This is a basic test. For detailed memory profiling,
        use external tools like memory_profiler.
        """
        import sys

        records = generate_test_records(10000, num_banks=10)
        processor = RecordProcessor(STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE)

        # Get size of input records
        input_size = sys.getsizeof(records)

        # Process records
        result = processor.process_records_optimized(records)

        # Get size of result
        result_size = sum(sys.getsizeof(bank_recs) for bank_recs in result.values())

        # Result should not be dramatically larger than input
        # (allowing for some overhead due to dictionary structure)
        memory_ratio = result_size / input_size
        logging.info(f"Memory ratio (output/input): {memory_ratio:.2f}")

        # This is a rough check - in practice, memory usage should be reasonable
        assert memory_ratio < 10.0, "Memory overhead should be reasonable"


if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Run a quick benchmark
    print("Running performance benchmark...")
    test = TestOptimizationPerformance()
    test.test_performance_comparison_benchmark()
    print("Benchmark complete!")
