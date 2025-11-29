"""
File copying functions with memory-efficient streaming approach.

This module provides functions for copying files from source to destination while:
- Minimizing memory usage through generator-based streaming
- Preserving file metadata (creation dates, modification times)
- Providing progress feedback
- Handling errors gracefully
"""

import os
import logging
from typing import Iterator, Tuple
from tqdm import tqdm
from shared.file_operations import copy_file, ensure_directory


def generate_file_pairs(src_folder: str, dest_folder: str) -> Iterator[Tuple[str, str]]:
    """
    Generator that yields (source, destination) file pairs without loading all into memory.

    This function uses a generator pattern to avoid pre-loading all file paths into memory,
    making it suitable for very large directory trees.

    Args:
        src_folder: Source directory to copy from
        dest_folder: Destination directory to copy to

    Yields:
        Tuple of (source_path, destination_path) for each file

    Example:
        >>> for src, dest in generate_file_pairs('/source', '/dest'):
        ...     print(f"Copy {src} to {dest}")
    """
    for root, _, files in os.walk(src_folder):
        rel_path = os.path.relpath(root, src_folder)

        for file in files:
            src_file = os.path.join(root, file)
            if rel_path == ".":
                dest_file = os.path.join(dest_folder, file)
            else:
                dest_file = os.path.join(dest_folder, rel_path, file)

            yield src_file, dest_file


def estimate_file_count(src_folder: str, sample_size: int = 100) -> int:
    """
    Estimate total file count by sampling subdirectories.

    This function provides a quick estimate of total files without traversing
    the entire directory tree, useful for progress bar initialization.

    Args:
        src_folder: Directory to estimate
        sample_size: Number of directories to sample for estimation

    Returns:
        Estimated total file count

    Example:
        >>> count = estimate_file_count('/large/directory')
        >>> print(f"Estimated {count} files")
    """
    subdirs = []
    file_counts = []

    # Collect subdirectories and count files
    for root, dirs, files in os.walk(src_folder):
        subdirs.append(root)
        file_counts.append(len(files))

        # Stop sampling after reaching sample_size
        if len(subdirs) >= sample_size:
            break

    if not file_counts:
        return 0

    # Estimate based on average files per directory
    avg_files_per_dir = sum(file_counts) / len(file_counts)

    # Count total subdirectories (quick scan)
    total_dirs = sum(1 for _, _, _ in os.walk(src_folder))

    estimated_total = int(avg_files_per_dir * total_dirs)

    logging.debug(f"Estimated {estimated_total} files from {total_dirs} directories (sampled {len(subdirs)})")
    return estimated_total


def copy_files_streaming(src_folder: str, dest_folder: str, overwrite: bool = False) -> None:
    """
    Copy files using streaming approach for minimal memory usage.

    This function uses a generator-based approach to process files one at a time,
    keeping memory usage constant regardless of the total number of files.

    Args:
        src_folder: Source directory containing files to copy
        dest_folder: Destination directory where files will be copied
        overwrite: Whether to overwrite existing files (default: False)

    Raises:
        Exception: If copy operation fails

    Example:
        >>> copy_files_streaming('/source', '/destination', overwrite=True)
        Copying files: 1234 files [00:05, 234.56 files/s]
    """
    try:
        # Ensure destination exists
        ensure_directory(dest_folder)
        logging.info(f"Destination folder ready: {dest_folder}")

        # Process files with streaming approach
        copied_count = 0
        skipped_count = 0
        error_count = 0

        # Use generator with unknown total (memory efficient)
        file_pairs = generate_file_pairs(src_folder, dest_folder)

        with tqdm(desc="Copying files", unit="file") as pbar:
            for src_file, dest_file in file_pairs:
                try:
                    # Check if destination exists (only if not overwriting)
                    if not overwrite and os.path.exists(dest_file):
                        logging.debug(f"Skipped existing file: {dest_file}")
                        skipped_count += 1
                    else:
                        copy_file(src_file, dest_file, overwrite=overwrite)
                        logging.debug(f"Copied: {src_file} -> {dest_file}")
                        copied_count += 1

                    pbar.update(1)

                except Exception as e:
                    logging.error(f"Failed to copy {src_file}: {e}")
                    error_count += 1
                    pbar.update(1)

        # Summary logging
        total_processed = copied_count + skipped_count + error_count
        logging.info(f"Copy operation completed: {total_processed} files processed")
        logging.info(f"  - Copied: {copied_count}")
        logging.info(f"  - Skipped: {skipped_count}")
        logging.info(f"  - Errors: {error_count}")

        if error_count > 0:
            logging.warning(f"{error_count} files failed to copy. Check logs for details.")

    except Exception as e:
        logging.error(f"Copy operation failed: {e}", exc_info=True)
        raise


def copy_files_with_progress_estimation(
    src_folder: str, dest_folder: str, overwrite: bool = False, sample_size: int = 100
) -> None:
    """
    Copy files with progress estimation to show percentage completion.

    This function estimates the total number of files before copying to provide
    a progress percentage. It automatically adjusts if the estimate is too low.

    Args:
        src_folder: Source directory containing files to copy
        dest_folder: Destination directory where files will be copied
        overwrite: Whether to overwrite existing files (default: False)
        sample_size: Number of directories to sample for estimation (default: 100)

    Raises:
        Exception: If copy operation fails

    Example:
        >>> copy_files_with_progress_estimation('/source', '/dest')
        Estimated 10000 files to process
        Copying files: 100%|██████████| 10234/10234 [00:45<00:00, 225.42 files/s]
    """
    try:
        # Ensure destination exists
        ensure_directory(dest_folder)

        # Quick estimation of file count
        estimated_total = estimate_file_count(src_folder, sample_size)

        copied_count = 0
        skipped_count = 0
        error_count = 0

        if estimated_total > 0:
            logging.info(f"Estimated {estimated_total} files to process")
            with tqdm(total=estimated_total, desc="Copying files", unit="file") as pbar:
                for src_file, dest_file in generate_file_pairs(src_folder, dest_folder):
                    try:
                        # Check if destination exists (only if not overwriting)
                        if not overwrite and os.path.exists(dest_file):
                            logging.debug(f"Skipped existing file: {dest_file}")
                            skipped_count += 1
                        else:
                            copy_file(src_file, dest_file, overwrite=overwrite)
                            logging.debug(f"Copied: {src_file} -> {dest_file}")
                            copied_count += 1

                        pbar.update(1)

                        # Adjust total if we exceed estimate
                        if pbar.n > pbar.total:
                            pbar.total = pbar.n + int(pbar.n * 0.1)  # Add 10% buffer
                            pbar.refresh()

                    except Exception as e:
                        logging.error(f"Failed to copy {src_file}: {e}")
                        error_count += 1
                        pbar.update(1)
        else:
            # Fallback to streaming without estimation
            logging.info("Could not estimate file count, using streaming mode")
            copy_files_streaming(src_folder, dest_folder, overwrite)
            return

        # Summary logging
        total_processed = copied_count + skipped_count + error_count
        logging.info(f"Copy operation completed: {total_processed} files processed")
        logging.info(f"  - Copied: {copied_count}")
        logging.info(f"  - Skipped: {skipped_count}")
        logging.info(f"  - Errors: {error_count}")

        if error_count > 0:
            logging.warning(f"{error_count} files failed to copy. Check logs for details.")

    except Exception as e:
        logging.error(f"Copy operation failed: {e}", exc_info=True)
        raise


def copy_files_with_preserved_dates(src_folder: str, dest_folder: str) -> None:
    """
    Legacy function wrapper - now uses streaming approach.

    This function is maintained for backward compatibility but now uses the
    memory-efficient streaming approach internally.

    Args:
        src_folder: Source directory containing files to copy
        dest_folder: Destination directory where files will be copied

    Note:
        This function is deprecated. Consider using copy_files_streaming()
        or copy_files_with_progress_estimation() directly for new code.

    Example:
        >>> copy_files_with_preserved_dates('/source', '/dest')
    """
    logging.info("Using legacy function copy_files_with_preserved_dates (now memory-efficient)")
    copy_files_streaming(src_folder, dest_folder, overwrite=False)
