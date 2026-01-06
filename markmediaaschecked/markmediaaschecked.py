#!/usr/bin/env python
"""
MarkMediaAsChecked - Script to mark media as checked in CSV files.

This script replaces STATUS_READY with STATUS_CHECKED in status columns
of a CSV file containing photo metadata.
"""
import os
import argparse
import logging
from datetime import datetime

from shared.utils import get_log_filename
from shared.file_operations import ensure_directory, load_csv, save_csv, move_file
from shared.logging_config import setup_logging

from markmediaascheckedlib.constants import DEFAULT_PHOTO_CSV_FILE, STATUS_READY, STATUS_CHECKED
from markmediaascheckedlib.mark_handler import (
    extract_status_columns,
    filter_ready_records,
    filter_records_by_edit_type,
    update_statuses
)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Mark media as checked in CSV files."
    )
    parser.add_argument(
        "--photo_csv_file",
        type=str,
        default=DEFAULT_PHOTO_CSV_FILE,
        help="Path to the CSV file containing photo metadata"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output file if it exists"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--log_dir",
        type=str,
        default="./logs",
        help="Directory for log files"
    )
    parser.add_argument(
        "--include-edited",
        action="store_true",
        help="Include edited photos from 'upravenĂ©' folders (default: only original photos)"
    )
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
    all_records = load_csv(args.photo_csv_file)
    if not all_records:
        logging.error(f"No records found in {args.photo_csv_file}")
        return

    # 2. Filter by edit type for processing (exclude alternative edits, optionally exclude edited photos)
    # Note: This creates a filtered VIEW for processing, but we keep all_records for saving
    records_to_process = filter_records_by_edit_type(all_records, include_edited=args.include_edited)
    if not records_to_process:
        logging.info("No records to process after filtering")
        return

    # 3. Find status columns
    status_columns = extract_status_columns(all_records)
    if args.banks:
        status_columns = _filter_status_columns(status_columns, _parse_banks(args.banks))
    if not status_columns:
        logging.error("No status columns found in the CSV file")
        return

    # 4. Filter records with STATUS_READY status (from processable records only)
    ready_records = filter_ready_records(records_to_process, status_columns)
    if not ready_records:
        logging.info(f"No records with '{STATUS_READY}' status found in processable records")
        return

    # 5. Update statuses from STATUS_READY to STATUS_CHECKED (only in ready_records, which are references to all_records)
    changes_count = update_statuses(ready_records, status_columns)
    logging.info(f"Updated {changes_count} status values in {len(ready_records)} records")

    # 6. Backup original file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = f"{args.photo_csv_file}.{timestamp}.old"
    logging.info(f"Backing up original file to {backup_path}")
    move_file(args.photo_csv_file, backup_path, overwrite=args.overwrite)

    # 7. Save updated CSV (save ALL records, including filtered ones)
    logging.info(f"Saving updated CSV to {args.photo_csv_file}")
    save_csv(all_records, args.photo_csv_file)

    logging.info("MarkMediaAsChecked process completed successfully")


def _parse_banks(banks_value: str) -> list[str]:
    """
    Parse a comma-separated bank list.
    """
    return [item.strip() for item in banks_value.split(",") if item.strip()]


def _filter_status_columns(status_columns: list[str], banks: list[str]) -> list[str]:
    """
    Filter status columns to selected banks.
    """
    if not banks:
        return status_columns

    filtered: list[str] = []
    lower_columns = {col.lower(): col for col in status_columns}

    for bank in banks:
        matched = False
        for col_lower, col in lower_columns.items():
            if col_lower.startswith(bank.lower()):
                filtered.append(col)
                matched = True
        if not matched:
            logging.warning("No status column found for bank: %s", bank)

    return filtered


if __name__ == "__main__":
    main()

