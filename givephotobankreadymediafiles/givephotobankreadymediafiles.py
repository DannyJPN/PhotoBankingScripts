#!/usr/bin/env python
"""
Give Photobank Ready Media Files - Orchestrator for preparing media files for photobanks.
"""
import os
import sys
import argparse
import logging

from shared.logging_config import setup_logging
from shared.file_operations import ensure_directory, read_json
from shared.config import get_config
from givephotobankreadymediafileslib.constants import (
    DEFAULT_MEDIA_CSV_PATH, DEFAULT_CATEGORIES_CSV_PATH, DEFAULT_LOG_DIR, 
    DEFAULT_PROCESSED_MEDIA_MAX_COUNT, DEFAULT_INTERVAL,
    DEFAULT_BATCH_MODE, DEFAULT_BATCH_SIZE, DEFAULT_BATCH_WAIT_TIMEOUT,
    DEFAULT_BATCH_POLL_INTERVAL, BATCH_LOCK_FILE
)
from givephotobankreadymediafileslib.mediainfo_loader import (
    load_media_records, load_categories
)
from givephotobankreadymediafileslib.media_processor import (
    find_unprocessed_records
)
from givephotobankreadymediafileslib.media_helper import (
    process_unmatched_files
)
from givephotobankreadymediafileslib.constants import BATCH_REGISTRY_FILE, COL_PATH
from givephotobankreadymediafileslib.batch_manager import run_batch_mode, check_batch_statuses
from givephotobankreadymediafileslib.batch_lock import BatchLock


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Orchestrate metadata generation for photobank media files."
    )
    parser.add_argument("--media_csv", type=str, default=DEFAULT_MEDIA_CSV_PATH,
                        help="Path to the media CSV file")
    parser.add_argument("--categories_csv", type=str, default=DEFAULT_CATEGORIES_CSV_PATH,
                        help="Path to the categories CSV file")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--max_count", type=int, default=DEFAULT_PROCESSED_MEDIA_MAX_COUNT,
                        help=f"Maximum number of files to process (default: {DEFAULT_PROCESSED_MEDIA_MAX_COUNT})")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help=f"Interval in seconds between processing files (default: {DEFAULT_INTERVAL})")
    parser.add_argument("--batch_mode", action="store_true", default=DEFAULT_BATCH_MODE,
                        help="Enable batch mode (collect descriptions, send batch to AI)")
    parser.add_argument("--batch_size", type=int, default=DEFAULT_BATCH_SIZE,
                        help=f"Total files to collect per run (default: {DEFAULT_BATCH_SIZE})")
    parser.add_argument("--batch_wait_timeout", type=int, default=DEFAULT_BATCH_WAIT_TIMEOUT,
                        help="Optional wait time for batch completion in seconds (default: 3600, 0 = unlimited)")
    parser.add_argument("--batch_poll_interval", type=int, default=DEFAULT_BATCH_POLL_INTERVAL,
                        help=f"Batch poll interval in seconds (default: {DEFAULT_BATCH_POLL_INTERVAL})")
    parser.add_argument("--check_batch_status", action="store_true",
                        help="Print status of active batches and exit")

    return parser.parse_args()


def main():
    """Main orchestrator function."""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    ensure_directory(args.log_dir)
    log_file = os.path.join(args.log_dir, "givephotobankreadymediafiles.log")
    setup_logging(debug=args.debug, log_file=log_file)
    
    # Initialize global configuration early for all modules
    config = get_config()
    logging.info("Global configuration loaded")
    
    # Log startup
    logging.info("Starting givephotobankreadymediafiles.py orchestrator")

    if args.check_batch_status:
        for line in check_batch_statuses():
            print(line)
        return 0

    if args.batch_mode:
        lock = BatchLock(BATCH_LOCK_FILE)
        try:
            lock.acquire()
        except RuntimeError as e:
            logging.error(str(e))
            print(str(e))
            return 1

        try:
            run_batch_mode(
                media_csv=args.media_csv,
                batch_size=args.batch_size,
                wait_timeout=args.batch_wait_timeout,
                poll_interval=args.batch_poll_interval
            )
            return 0
        finally:
            lock.release()
    
    # Load media records
    media_records = load_media_records(args.media_csv)
    if not media_records:
        logging.error("No media records found")
        print("Error: No media records found")
        return 1
    
    # Load categories
    categories = load_categories(args.categories_csv)
    if not categories:
        logging.warning("No categories loaded, continuing without categories")
    
    # Find unprocessed records
    unprocessed_records = find_unprocessed_records(media_records)

    # Skip files that are already in active batches (batch/manual conflict guard)
    registry_data = read_json(BATCH_REGISTRY_FILE, default={})
    active_files = set(registry_data.get("file_registry", {}).keys())
    if active_files:
        filtered = []
        skipped = 0
        for record in unprocessed_records:
            file_path = record.get(COL_PATH, "")
            normalized = os.path.abspath(file_path).replace("\\", "/") if file_path else ""
            if file_path and normalized in active_files:
                skipped += 1
                continue
            filtered.append(record)
        unprocessed_records = filtered
        if skipped:
            logging.info("Skipped %d files (in active batch).", skipped)
            print(f"Skipped {skipped} files (in active batch).")
    
    if not unprocessed_records:
        logging.info("No unprocessed records found. All files are up to date.")
        print("No unprocessed records found. All files are up to date.")
        return 0
    
    logging.info(f"Found {len(unprocessed_records)} files to process")
    print(f"Found {len(unprocessed_records)} files to process")
    
    # Process files sequentially with user-specified limits
    stats = process_unmatched_files(unprocessed_records, config=config, 
                                   max_count=args.max_count, interval=args.interval, 
                                   media_csv=args.media_csv)
    
    # Summary
    total_attempted = stats['processed'] + stats['failed']
    if total_attempted > 0:
        print(f"\nProcessing complete:")
        print(f"  Processed: {stats['processed']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Skipped: {stats['skipped']}")
        
        return 0 if stats['failed'] == 0 else 1
    else:
        print("No files were processed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
