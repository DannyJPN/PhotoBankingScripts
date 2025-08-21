"""
Performance tests for camera detection regex operations.

:author: SortUnsortedMedia Test Suite
:date: 2025-08-21
"""

import unittest
import time
import re
from typing import List
from sortunsortedmedialib.constants import CAMERA_REGEXES


class TestCameraDetectionRegexPerformanceBenchmarks(unittest.TestCase):
    """Test performance characteristics of camera detection regex operations."""

    def setUp(self) -> None:
        """Set up test fixtures with large datasets."""
        # Create test datasets of different sizes
        self.small_dataset = self._generate_test_filenames(100)
        self.medium_dataset = self._generate_test_filenames(1000)
        self.large_dataset = self._generate_test_filenames(10000)
        
        # Pre-compile regex patterns for performance testing
        self.compiled_patterns = {
            pattern: re.compile(pattern) 
            for pattern in CAMERA_REGEXES.keys()
        }

    def _generate_test_filenames(self, count: int) -> List[str]:
        """
        Generate test filenames for performance testing.
        
        :param count: Number of filenames to generate
        :return: List of test filenames
        """
        filenames = []
        patterns = [
            "DSC{:05d}",  # Sony pattern
            "IMG{:014d}",  # Realme pattern  
            "{:08d}_{:06d}",  # Samsung pattern
            "SAM_{:04d}",  # Samsung ES9 pattern
            "NIK_{:04d}",  # Nikon pattern
            "DJI_{:014d}_{:04d}_W",  # DJI pattern
            "PICT{:04d}",  # Bunaty pattern
            "unknown_{:04d}",  # Unknown pattern
        ]
        
        for i in range(count):
            pattern = patterns[i % len(patterns)]
            if pattern == "IMG{:014d}":
                filename = pattern.format(20220101000000 + i)
            elif pattern == "{:08d}_{:06d}":
                filename = pattern.format(20220101 + i // 10000, 120000 + i % 86400)
            elif pattern == "DJI_{:014d}_{:04d}_W":
                filename = pattern.format(20220101000000 + i, i % 10000)
            else:
                filename = pattern.format(i)
            filenames.append(filename)
            
        return filenames

    def test_camera_detection__regex_performance__small_dataset_timing(self) -> None:
        """Test regex performance on small dataset (100 files)."""
        start_time = time.time()
        
        matches = 0
        for filename in self.small_dataset:
            for pattern in CAMERA_REGEXES.keys():
                if re.match(pattern, filename):
                    matches += 1
                    break
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should process 100 files quickly
        self.assertLess(execution_time, 0.1, 
                       f"Should process {len(self.small_dataset)} files in < 0.1s, took {execution_time:.4f}s")
        self.assertGreater(matches, 0, "Should find some matches in test dataset")

    def test_camera_detection__regex_performance__medium_dataset_timing(self) -> None:
        """Test regex performance on medium dataset (1000 files)."""
        start_time = time.time()
        
        matches = 0
        for filename in self.medium_dataset:
            for pattern in CAMERA_REGEXES.keys():
                if re.match(pattern, filename):
                    matches += 1
                    break
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should process 1000 files reasonably quickly
        self.assertLess(execution_time, 1.0, 
                       f"Should process {len(self.medium_dataset)} files in < 1.0s, took {execution_time:.4f}s")
        self.assertGreater(matches, 0, "Should find some matches in test dataset")

    def test_camera_detection__regex_performance__large_dataset_timing(self) -> None:
        """Test regex performance on large dataset (10000 files)."""
        start_time = time.time()
        
        matches = 0
        for filename in self.large_dataset:
            for pattern in CAMERA_REGEXES.keys():
                if re.match(pattern, filename):
                    matches += 1
                    break
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should process 10000 files within reasonable time (10 minutes max per CLAUDE.md)
        self.assertLess(execution_time, 600, 
                       f"Should process {len(self.large_dataset)} files in < 10 minutes, took {execution_time:.4f}s")
        self.assertGreater(matches, 0, "Should find some matches in test dataset")
        
        # Log performance metrics
        files_per_second = len(self.large_dataset) / execution_time
        print(f"Performance: {files_per_second:.0f} files/second on large dataset")

    def test_camera_detection__regex_performance__compiled_vs_uncompiled(self) -> None:
        """Test performance difference between compiled and uncompiled regex patterns."""
        test_filename = "DSC00001"
        iterations = 10000
        
        # Test uncompiled regex
        start_time = time.time()
        for _ in range(iterations):
            for pattern in CAMERA_REGEXES.keys():
                re.match(pattern, test_filename)
        uncompiled_time = time.time() - start_time
        
        # Test compiled regex
        start_time = time.time()
        for _ in range(iterations):
            for compiled_pattern in self.compiled_patterns.values():
                compiled_pattern.match(test_filename)
        compiled_time = time.time() - start_time
        
        # Compiled should be faster (or at least not significantly slower)
        speedup_ratio = uncompiled_time / compiled_time if compiled_time > 0 else float('inf')
        
        self.assertGreater(speedup_ratio, 0.8, 
                          f"Compiled regex should not be significantly slower. Ratio: {speedup_ratio:.2f}")
        
        print(f"Regex compilation speedup: {speedup_ratio:.2f}x")

    def test_camera_detection__regex_performance__pattern_complexity_analysis(self) -> None:
        """Test performance impact of different regex pattern complexities."""
        test_iterations = 1000
        test_filename = "DJI_20220101123456_0001_W"  # Complex pattern
        
        # Test each pattern individually to identify performance bottlenecks
        pattern_times = {}
        
        for pattern, camera_name in CAMERA_REGEXES.items():
            start_time = time.time()
            
            for _ in range(test_iterations):
                re.match(pattern, test_filename)
                
            pattern_time = time.time() - start_time
            pattern_times[camera_name] = pattern_time
        
        # Find slowest patterns
        sorted_patterns = sorted(pattern_times.items(), key=lambda x: x[1], reverse=True)
        slowest_pattern = sorted_patterns[0]
        fastest_pattern = sorted_patterns[-1]
        
        # Log performance analysis
        print(f"Slowest pattern: {slowest_pattern[0]} ({slowest_pattern[1]:.6f}s)")
        print(f"Fastest pattern: {fastest_pattern[0]} ({fastest_pattern[1]:.6f}s)")
        
        # Ensure no pattern is extremely slow
        max_acceptable_time = 0.01  # 10ms for 1000 iterations
        for camera_name, pattern_time in pattern_times.items():
            self.assertLess(pattern_time, max_acceptable_time,
                           f"Pattern for {camera_name} too slow: {pattern_time:.6f}s > {max_acceptable_time}s")

    def test_camera_detection__regex_performance__memory_usage_stability(self) -> None:
        """Test that regex operations don't cause memory leaks or excessive usage."""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform many regex operations
        for _ in range(1000):
            for filename in self.small_dataset[:10]:  # Use subset to avoid timeout
                for pattern in CAMERA_REGEXES.keys():
                    match = re.match(pattern, filename)
                    if match:
                        break
        
        # Force garbage collection after test
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Check that object count hasn't grown excessively
        object_growth = final_objects - initial_objects
        growth_percentage = (object_growth / initial_objects) * 100 if initial_objects > 0 else 0
        
        self.assertLess(growth_percentage, 50, 
                       f"Memory usage grew by {growth_percentage:.1f}%, should be < 50%")

    def test_camera_detection__regex_performance__concurrent_safety(self) -> None:
        """Test regex performance under concurrent access patterns."""
        import threading
        import queue
        
        # Shared queue for results
        results_queue = queue.Queue()
        
        def worker_thread(filenames: List[str], thread_id: int) -> None:
            """Worker thread for concurrent regex testing."""
            start_time = time.time()
            matches = 0
            
            for filename in filenames:
                for pattern in CAMERA_REGEXES.keys():
                    if re.match(pattern, filename):
                        matches += 1
                        break
            
            end_time = time.time()
            results_queue.put((thread_id, end_time - start_time, matches))
        
        # Create multiple threads
        thread_count = 4
        threads = []
        chunk_size = len(self.medium_dataset) // thread_count
        
        start_time = time.time()
        
        for i in range(thread_count):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < thread_count - 1 else len(self.medium_dataset)
            chunk = self.medium_dataset[start_idx:end_idx]
            
            thread = threading.Thread(target=worker_thread, args=(chunk, i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        thread_times = []
        total_matches = 0
        
        while not results_queue.empty():
            thread_id, thread_time, matches = results_queue.get()
            thread_times.append(thread_time)
            total_matches += matches
        
        # Verify concurrent execution was successful
        self.assertEqual(len(thread_times), thread_count, "All threads should complete")
        self.assertGreater(total_matches, 0, "Should find matches across all threads")
        
        # Concurrent execution should be faster than sequential
        avg_thread_time = sum(thread_times) / len(thread_times)
        efficiency = avg_thread_time / total_time if total_time > 0 else 0
        
        print(f"Concurrent efficiency: {efficiency:.2f} (higher is better)")
        self.assertGreater(efficiency, 0.5, "Concurrent execution should show some efficiency gain")


if __name__ == "__main__":
    unittest.main()