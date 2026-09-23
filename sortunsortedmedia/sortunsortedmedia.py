#!/usr/bin/env python3


"""
Main script for processing and sorting unsorted media files.
"""

import os
import argparse
import logging
from pathlib import Path

from shared.utils import get_log_filename
from shared.file_operations import ensure_directory, save_csv, save_json
from shared.logging_config import setup_logging

from sortunsortedmedialib.constants import (
    DEFAULT_UNSORTED_FOLDER,
    DEFAULT_TARGET_FOLDER,
    DEFAULT_INTERVAL,
    DEFAULT_MAX_PARALLEL,
    DEFAULT_REPORT_DIR,
    DEFAULT_REPORT_FORMAT,
)
from sortunsortedmedialib.media_helper import find_unmatched_media, process_unmatched_files
from sortunsortedmedialib.reporting import (
    build_detail_records,
    build_report_filename,
    build_summary_records,
)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process and sort unsorted media files."
    )
    parser.add_argument("--unsorted_folder", type=str, default=DEFAULT_UNSORTED_FOLDER,
                        help="Folder containing unsorted media files")
    parser.add_argument("--target_folder", type=str, default=DEFAULT_TARGET_FOLDER,
                        help="Target folder for sorted media")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help="Interval in seconds to wait between processing files")
    parser.add_argument("--max_parallel", type=int, default=DEFAULT_MAX_PARALLEL,
                        help=f"Maximum number of parallel processes (default: {DEFAULT_MAX_PARALLEL})")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate reports without launching processing")
    parser.add_argument("--report-dir", type=str, default=DEFAULT_REPORT_DIR,
                        help="Directory for dry-run and summary reports")
    parser.add_argument("--report-format", type=str, default=DEFAULT_REPORT_FORMAT,
                        choices=["csv", "json"], help="Report format: csv or json")
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_arguments()

    # Setup logging
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    ensure_directory(log_dir)
    log_file = get_log_filename(log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    logging.info("Starting unsorted media processing")
    logging.info(f"Unsorted folder: {args.unsorted_folder}")
    logging.info(f"Target folder: {args.target_folder}")

    # Find unmatched media files
    unmatched_categories = find_unmatched_media(args.unsorted_folder, args.target_folder)
    
    # Process categories in order: JPG, other images, videos, edited images, edited videos
    category_order = ['jpg_files', 'other_images', 'videos', 'edited_images', 'edited_videos']
    
    total_files = sum(len(files) for files in unmatched_categories.values())
    if total_files == 0:
        print("No unmatched media files found.")
        logging.info("No unmatched media files found")
        if args.dry_run:
            write_reports(unmatched_categories, args.report_dir, args.report_format)
        return

    print(f"\n=== Found {total_files} unmatched media files ===")

    if args.dry_run:
        write_reports(unmatched_categories, args.report_dir, args.report_format)
        logging.info("Dry-run enabled, skipping processing")
        print("\nDry-run complete. No files were processed.")
        return
    
    for category in category_order:
        files = unmatched_categories[category]
        if not files:
            continue
            
        category_name = category.replace('_', ' ').title()
        logging.info(f"Processing {len(files)} {category_name}")
        print(f"\n=== Processing {len(files)} {category_name} ===")


        process_unmatched_files(files, args.target_folder, args.interval, args.max_parallel)

    logging.info("Unsorted media processing completed")
    print("\nAll media processing completed!")


def resolve_report_dir(report_dir: str) -> str:
    """
    Normalize and validate the report directory path.

    Args:
        report_dir: User-supplied report directory path.

    Returns:
        Normalized absolute directory path.

    Raises:
        ValueError: If the path is empty or points to an existing file.
    """
    if not report_dir or not report_dir.strip():
        raise ValueError("Report directory path must not be empty.")

    resolved = Path(report_dir).expanduser().resolve(strict=False)
    if resolved.exists() and not resolved.is_dir():
        raise ValueError(f"Report directory points to an existing file: {resolved}")
    return str(resolved)


def write_reports(unmatched_categories: dict[str, list[str]], report_dir: str, report_format: str) -> None:
    """
    Write dry-run detail and summary reports.

    Args:
        unmatched_categories: Mapping of category name to list of file paths.
        report_dir: Directory where the report will be saved.
        report_format: Output format, either 'csv' or 'json'.
    """
    resolved_report_dir = resolve_report_dir(report_dir)
    detail_records = build_detail_records(unmatched_categories)
    summary_records = build_summary_records(unmatched_categories)
    detail_name = build_report_filename("SortUnsortedMediaDryRun", report_format)
    summary_name = build_report_filename("SortUnsortedMediaSummary", report_format)
    detail_path = os.path.join(resolved_report_dir, detail_name)
    summary_path = os.path.join(resolved_report_dir, summary_name)

    try:
        if report_format == "csv":
            save_csv(detail_records, detail_path, ["category", "file_path"])
            save_csv(summary_records, summary_path, ["category", "count"])
        else:
            save_json({"records": detail_records}, detail_path)
            save_json({"records": summary_records}, summary_path)
    except Exception:
        logging.exception("Failed to write dry-run reports to %s", resolved_report_dir)
        raise

    logging.info("Dry-run detail report saved to %s", detail_path)
    logging.info("Dry-run summary report saved to %s", summary_path)

if __name__ == "__main__":
    main()
