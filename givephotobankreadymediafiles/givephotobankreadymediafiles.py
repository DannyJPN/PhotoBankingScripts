#!/usr/bin/env python
"""
Give Photobank Ready Media Files - Orchestrator for preparing media files for photobanks.
"""
import os
import sys
import argparse
import logging

from shared.logging_config import setup_logging
from shared.file_operations import ensure_directory
from givephotobankreadymediafileslib.constants import (
    DEFAULT_MEDIA_CSV_PATH, DEFAULT_CATEGORIES_CSV_PATH, DEFAULT_LOG_DIR
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
    
    return parser.parse_args()


def main():
    """Main orchestrator function."""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    ensure_directory(args.log_dir)
    log_file = os.path.join(args.log_dir, "givephotobankreadymediafiles.log")
    setup_logging(debug=args.debug, log_file=log_file)
    
    # Log startup
    logging.info("Starting givephotobankreadymediafiles.py orchestrator")
    
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
    
    if not unprocessed_records:
        logging.info("No unprocessed records found. All files are up to date.")
        print("No unprocessed records found. All files are up to date.")
        return 0
    
    logging.info(f"Found {len(unprocessed_records)} files to process")
    print(f"Found {len(unprocessed_records)} files to process")
    
    # Process files sequentially (default: max 1 file like PowerShell)
    stats = process_unmatched_files(unprocessed_records, max_count=1)
    
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