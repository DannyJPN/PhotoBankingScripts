"""
Mark Photo Media Approval Status

This script allows manual evaluation of photo statuses in a CSV database for each defined photobank.
It displays information about the photo, asks the user if the photo was approved,
and saves the result back to the CSV and to a log.
"""

import argparse
import logging

from shared.utils import get_log_filename
from shared.file_operations import ensure_directory, load_csv
from shared.logging_config import setup_logging

from markphotomediaapprovalstatuslib.constants import (
    DEFAULT_PHOTO_CSV_PATH,
    DEFAULT_LOG_DIR,
    STATUS_CHECKED,
)
from markphotomediaapprovalstatuslib.status_handler import (
    filter_checked_entries,
    filter_records_by_edit_type,
)
from markphotomediaapprovalstatuslib.media_helper import process_approval_records


def parse_arguments():
    """Parse command line arguments.

    :return: Parsed argument namespace.
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
    parser.add_argument("--include-edited", action="store_true",
                        help="Include edited photos from 'upravené' folders (default: only original photos)")
    return parser.parse_args()


def main() -> None:
    """Entry point: load CSV, run GUI approval flow, and save results."""
    args = parse_arguments()

    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)
    logging.info("Starting photo media approval status marking process")

    try:
        all_data = load_csv(args.csv_path)
        logging.info("Loaded %s records from %s", len(all_data), args.csv_path)
    except Exception as exc:
        logging.error("Failed to load CSV file: %s", exc)
        return

    data_to_process = filter_records_by_edit_type(all_data, include_edited=args.include_edited)
    if not data_to_process:
        logging.info("No records to process after filtering")
        return

    filtered_data = filter_checked_entries(data_to_process)
    if not filtered_data:
        logging.info("No entries with '%s' status found in processable records. Nothing to process.", STATUS_CHECKED)
        return

    changes_made = process_approval_records(all_data, filtered_data, args.csv_path)

    if changes_made:
        logging.info("All changes have been saved during processing")
    else:
        logging.info("No changes were made")

    logging.info("Photo media approval status marking process completed")


if __name__ == "__main__":
    main()
