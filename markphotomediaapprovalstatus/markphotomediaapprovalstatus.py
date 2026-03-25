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
    filter_checked_entries,
    filter_records_by_edit_type
)
from markphotomediaapprovalstatuslib.media_helper import process_approval_records
from markphotomediaapprovalstatuslib.public_portfolio.runner import process_public_portfolio_approval
from markphotomediaapprovalstatuslib.public_portfolio.constants import DEFAULT_PUBLIC_PORTFOLIO_CONFIG


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
    parser.add_argument("--public-portfolio-approval", action="store_true",
                        help="Enable public-portfolio approval detection mode (no GUI, no login)")
    parser.add_argument("--public-portfolio-config", type=str, default=DEFAULT_PUBLIC_PORTFOLIO_CONFIG,
                        help="Path to public portfolio config JSON")
    parser.add_argument("--public-visible", action="store_true",
                        help="Run browser with visible UI for public-portfolio detection")
    parser.add_argument("--public-discover-only", action="store_true",
                        help="Only discover portfolio URLs/identities and save config (no status updates)")
    parser.add_argument("--public-dry-run", action="store_true",
                        help="Run portfolio approval detection but do not write any changes to PhotoMedia.csv")
    return parser.parse_args()


def main() -> None:
    """Entry point: load CSV, run approval detection or GUI, and save results."""
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)
    logging.info("Starting photo media approval status marking process")

    # Load CSV data
    try:
        all_data = load_csv(args.csv_path)
        logging.info(f"Loaded {len(all_data)} records from {args.csv_path}")
    except Exception as e:
        logging.error(f"Failed to load CSV file: {e}")
        return

    # Filter by edit type for processing (exclude alternative edits, optionally exclude edited photos)
    # Note: This creates a filtered VIEW for processing, but we keep all_data for saving
    data_to_process = filter_records_by_edit_type(all_data, include_edited=args.include_edited)
    if not data_to_process:
        logging.info("No records to process after filtering")
        return

    # Filter entries with STATUS_CHECKED status (from processable records only)
    filtered_data = filter_checked_entries(data_to_process)
    if not filtered_data:
        logging.info(f"No entries with '{STATUS_CHECKED}' status found in processable records. Nothing to process.")
        return

    if args.public_portfolio_approval:
        changes_made = process_public_portfolio_approval(
            all_data,
            filtered_data,
            args.csv_path,
            config_path=args.public_portfolio_config,
            headless=not args.public_visible,
            discover_only=args.public_discover_only,
            dry_run=args.public_dry_run,
        )
    else:
        # Process approval records using GUI (saves after each file)
        # Pass all_data so changes are made to the complete dataset
        changes_made = process_approval_records(all_data, filtered_data, args.csv_path)

    # Final summary (individual saves are done during processing)
    if changes_made:
        logging.info("All changes have been saved during processing")
    else:
        logging.info("No changes were made")

    logging.info("Photo media approval status marking process completed")


if __name__ == "__main__":
    main()
