"""
Mark Photo Media Approval Status

This script allows manual evaluation of photo statuses in a CSV database for each defined photobank.
It displays information about the photo, asks the user if the photo was approved,
and saves the result back to the CSV and to a log.
"""

import os
import argparse
import logging

from shared.utils import get_log_filename
from shared.file_operations import ensure_directory, load_csv, save_csv_with_backup
from shared.logging_config import setup_logging

from markphotomediaapprovalstatuslib.constants import (
    BANKS,
    DEFAULT_PHOTO_CSV_PATH,
    DEFAULT_LOG_DIR,
    STATUS_CHECKED,
    STATUS_COLUMN_KEYWORD,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_MAYBE
)
from markphotomediaapprovalstatuslib.status_handler import (
    filter_checked_entries
)
from markphotomediaapprovalstatuslib.media_helper import process_approval_records


def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Mark photo media approval status in CSV database."
    )
    parser.add_argument("--csv_path", type=str, default=DEFAULT_PHOTO_CSV_PATH,
                        help="Path to the CSV file with photo media data")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    return parser.parse_args()


def main():
    """
    Main function of the script.
    """
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)
    logging.info("Starting photo media approval status marking process")

    # Load CSV data
    try:
        data = load_csv(args.csv_path)
        logging.info(f"Loaded {len(data)} records from {args.csv_path}")
    except Exception as e:
        logging.error(f"Failed to load CSV file: {e}")
        return

    # Filter entries with STATUS_CHECKED status
    filtered_data = filter_checked_entries(data)
    if not filtered_data:
        logging.info(f"No entries with '{STATUS_CHECKED}' status found. Nothing to process.")
        return

    # Process approval records using GUI (saves after each file)
    changes_made = process_approval_records(data, filtered_data, args.csv_path)

    # Final summary (individual saves are done during processing)
    if changes_made:
        logging.info("All changes have been saved during processing")
    else:
        logging.info("No changes were made")

    logging.info("Photo media approval status marking process completed")


if __name__ == "__main__":
    main()
