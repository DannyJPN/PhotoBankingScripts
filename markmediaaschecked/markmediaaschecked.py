#!/usr/bin/env python
"""
MarkMediaAsChecked - Script to mark media as checked in CSV files.

This script replaces STATUS_READY with STATUS_CHECKED in status columns
of a CSV file containing photo metadata.
"""
import argparse
import logging

from markmediaascheckedlib.constants import DEFAULT_PHOTO_CSV_FILE, STATUS_READY
from markmediaascheckedlib.mark_handler import extract_status_columns, filter_ready_records, update_statuses
from shared.file_operations import ensure_directory, load_csv, save_csv_with_backup
from shared.logging_config import setup_logging
from shared.utils import get_log_filename


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Mark media as checked in CSV files.")
    parser.add_argument(
        "--photo_csv_file",
        type=str,
        default=DEFAULT_PHOTO_CSV_FILE,
        help="Path to the CSV file containing photo metadata",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output file if it exists")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--log_dir", type=str, default="./logs", help="Directory for log files")
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)
    logging.info("Starting MarkMediaAsChecked process")

    # 1. Load CSV file
    logging.info(f"Loading CSV file from {args.photo_csv_file}")
    records = load_csv(args.photo_csv_file)
    if not records:
        logging.error(f"No records found in {args.photo_csv_file}")
        return

    # 2. Find status columns
    status_columns = extract_status_columns(records)
    if not status_columns:
        logging.error("No status columns found in the CSV file")
        return

    # 3. Filter records with STATUS_READY status
    ready_records = filter_ready_records(records, status_columns)
    if not ready_records:
        logging.info(f"No records with '{STATUS_READY}' status found")
        return

    # 4. Update statuses from STATUS_READY to STATUS_CHECKED
    changes_count = update_statuses(records, status_columns)
    # Detailed logging is now handled in the update_status_values function

    # 5. Save updated CSV with backup
    save_csv_with_backup(records, args.photo_csv_file)

    logging.info("MarkMediaAsChecked process completed successfully")


if __name__ == "__main__":
    main()
