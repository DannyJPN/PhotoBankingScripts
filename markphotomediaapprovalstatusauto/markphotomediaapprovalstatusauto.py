"""Mark Photo Media Approval Status — automatic detection pipeline.

This script evaluates approval status of photos in PhotoMedia.csv for each
defined photobank.  Two modes are supported:

- Default (no flags): opens the GUI for manual evaluation.
- ``--auto``: runs the automatic detection pipeline (no GUI, no login).
"""

import argparse
import logging
import sys

from shared.file_operations import ensure_directory, load_csv
from shared.logging_config import setup_logging
from shared.utils import get_log_filename

from markphotomediaapprovalstatuslib.constants import (
    BANKS,
    DEFAULT_CONTRIBUTOR_NAME,
    DEFAULT_HASH_CACHE_PATH,
    DEFAULT_LOG_DIR,
    DEFAULT_PHOTO_CSV_PATH,
    DEFAULT_PREVIEW_CACHE_DIR,
    DEFAULT_REPORT_DIR,
    STATUS_CHECKED,
)
from markphotomediaapprovalstatuslib.discovery.registry import available_banks
from markphotomediaapprovalstatuslib.media_helper import process_approval_records
from markphotomediaapprovalstatuslib.pipeline import run_detection
from markphotomediaapprovalstatuslib.status_handler import (
    filter_checked_entries,
    filter_records_by_edit_type,
)


def _parse_banks(raw: str) -> list:
    """Parse a comma-separated bank list into a validated list.

    :param raw: Comma-separated bank names from the CLI.
    :return: Validated list of bank names.
    :raises argparse.ArgumentTypeError: If any name is not registered.
    """
    names = [b.strip() for b in raw.split(",") if b.strip()]
    known = set(available_banks())
    unknown = [n for n in names if n not in known]
    if unknown:
        raise argparse.ArgumentTypeError(f"Unknown banks: {unknown}. Available: {sorted(known)}")
    return names


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    :return: Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(description="Mark photo media approval status in CSV database.")
    parser.add_argument("--csv_path", type=str, default=DEFAULT_PHOTO_CSV_PATH, help="Path to PhotoMedia.csv")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR, help="Directory for log files")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--include-edited",
        action="store_true",
        help="Include edited photos from 'upravené' folders",
    )

    auto_group = parser.add_argument_group("automatic detection")
    auto_group.add_argument("--auto", action="store_true", help="Run automatic detection pipeline (no GUI)")
    auto_group.add_argument(
        "--banks",
        type=str,
        default=None,
        help="Comma-separated bank names to process (default: all)",
    )
    auto_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Run detection but do not write changes to PhotoMedia.csv",
    )
    auto_group.add_argument(
        "--report-dir",
        type=str,
        default=DEFAULT_REPORT_DIR,
        help="Directory for audit report CSV",
    )
    auto_group.add_argument(
        "--contributor-name",
        type=str,
        default=DEFAULT_CONTRIBUTOR_NAME,
        help="Your contributor username used for identity matching",
    )
    auto_group.add_argument("--visible", action="store_true", help="Show browser window during detection")
    auto_group.add_argument(
        "--hash-cache",
        type=str,
        default=DEFAULT_HASH_CACHE_PATH,
        help="Path to SQLite hash cache file",
    )
    auto_group.add_argument(
        "--preview-cache-dir",
        type=str,
        default=DEFAULT_PREVIEW_CACHE_DIR,
        help="Directory for caching downloaded preview images",
    )

    return parser.parse_args()


def main() -> None:
    """Entry point: load CSV, run detection or GUI, and save results."""
    args = parse_arguments()

    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)
    logging.info("Starting photo media approval status marking process")

    try:
        all_data = load_csv(args.csv_path)
        logging.info("Loaded %d records from %s", len(all_data), args.csv_path)
    except Exception as exc:
        logging.error("Failed to load CSV: %s", exc)
        sys.exit(1)

    data_to_process = filter_records_by_edit_type(all_data, include_edited=args.include_edited)
    if not data_to_process:
        logging.info("No records to process after filtering")
        return

    filtered_data = filter_checked_entries(data_to_process)
    if not filtered_data:
        logging.info("No entries with '%s' status found. Nothing to process.", STATUS_CHECKED)
        return

    if args.auto:
        banks = BANKS
        if args.banks:
            try:
                banks = _parse_banks(args.banks)
            except argparse.ArgumentTypeError as exc:
                logging.error("%s", exc)
                sys.exit(1)

        run_detection(
            all_data=all_data,
            filtered_data=filtered_data,
            csv_path=args.csv_path,
            banks=banks,
            contributor_name=args.contributor_name,
            dry_run=args.dry_run,
            report_dir=args.report_dir,
            headless=not args.visible,
            hash_cache_path=args.hash_cache,
            preview_cache_dir=args.preview_cache_dir,
        )
    else:
        process_approval_records(all_data, filtered_data, args.csv_path)

    logging.info("Photo media approval status marking process completed")


if __name__ == "__main__":
    main()