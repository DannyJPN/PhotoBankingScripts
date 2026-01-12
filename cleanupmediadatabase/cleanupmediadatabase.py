#!/usr/bin/env python3
"""
CleanupMediaDatabase - validate and clean PhotoMedia.csv against the file system.
"""

import argparse
import logging
import os
from typing import Dict, List

from shared.utils import get_log_filename
from shared.logging_config import setup_logging
from shared.file_operations import ensure_directory, load_csv, save_csv_with_backup, list_files, save_csv, save_json

from cleanupmediadatabaselib.constants import (
    DEFAULT_MEDIA_CSV_PATH,
    DEFAULT_PHOTO_DIR,
    DEFAULT_VIDEO_DIR,
    DEFAULT_LOG_DIR,
    DEFAULT_REPORT_DIR,
    DEFAULT_REPORT_FORMAT,
    COLUMN_PATH,
    COLUMN_FILENAME,
    DELETED_VALUE
)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Validate and clean PhotoMedia.csv against the file system."
    )
    parser.add_argument("--media_csv", type=str, default=DEFAULT_MEDIA_CSV_PATH,
                        help="Path to the media CSV database (PhotoMedia.csv)")
    parser.add_argument("--photo_dir", type=str, default=DEFAULT_PHOTO_DIR,
                        help="Directory containing photos")
    parser.add_argument("--video_dir", type=str, default=DEFAULT_VIDEO_DIR,
                        help="Directory containing videos")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--report-dir", type=str, default=DEFAULT_REPORT_DIR,
                        help="Directory for reports")
    parser.add_argument("--report-format", type=str, default=DEFAULT_REPORT_FORMAT,
                        choices=["csv", "json"], help="Report format: csv or json")
    parser.add_argument("--export-report", action="store_true",
                        help="Export validation report")
    parser.add_argument("--remove-missing", action="store_true",
                        help="Remove records with missing files from the CSV")
    parser.add_argument("--scan-media-dirs", action="store_true",
                        help="Scan media directories for files missing in the CSV")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    return parser.parse_args()


def main() -> int:
    """
    Main entry point.
    """
    args = parse_arguments()

    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    logging.info("Starting CleanupMediaDatabase")
    logging.info("Media CSV: %s", args.media_csv)

    if not os.path.exists(args.media_csv):
        logging.error("Media CSV not found: %s", args.media_csv)
        return 1

    records = load_csv(args.media_csv)
    if not records:
        logging.warning("No records found in %s", args.media_csv)
        return 0

    missing_records = _find_missing_records(records)
    missing_count = len(missing_records)

    removed_count = 0
    if args.remove_missing and missing_records:
        records = _remove_missing_records(records, missing_records)
        save_csv_with_backup(records, args.media_csv)
        removed_count = missing_count
        logging.info("Removed %d missing records", removed_count)

    orphan_files = []
    if args.scan_media_dirs:
        orphan_files = _find_orphan_files(records, [args.photo_dir, args.video_dir])

    if args.export_report:
        _write_report(
            missing_records,
            orphan_files,
            missing_count,
            removed_count,
            args.report_dir,
            args.report_format
        )

    logging.info("CleanupMediaDatabase completed")
    return 0


def _find_missing_records(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Find records whose file paths do not exist.
    """
    missing: List[Dict[str, str]] = []
    for record in records:
        path = record.get(COLUMN_PATH, "")
        if path and not os.path.exists(path):
            record["missing"] = DELETED_VALUE
            missing.append(record)
    logging.info("Found %d missing records", len(missing))
    return missing


def _remove_missing_records(
    records: List[Dict[str, str]],
    missing_records: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """
    Remove missing records from the dataset.
    """
    missing_set = {rec.get(COLUMN_PATH, "") for rec in missing_records}
    return [rec for rec in records if rec.get(COLUMN_PATH, "") not in missing_set]


def _find_orphan_files(records: List[Dict[str, str]], media_dirs: List[str]) -> List[str]:
    """
    Find files that exist on disk but are missing from the CSV.
    """
    known_paths = {rec.get(COLUMN_PATH, "") for rec in records if rec.get(COLUMN_PATH, "")}
    orphan_files: List[str] = []
    for directory in media_dirs:
        if not os.path.exists(directory):
            logging.warning("Media directory not found: %s", directory)
            continue
        for path in list_files(directory, recursive=True):
            if path not in known_paths:
                orphan_files.append(path)
    logging.info("Found %d orphan files", len(orphan_files))
    return orphan_files


def _write_report(
    missing_records: List[Dict[str, str]],
    orphan_files: List[str],
    missing_count: int,
    removed_count: int,
    report_dir: str,
    report_format: str
) -> None:
    """
    Write validation report to CSV or JSON.
    """
    report_data = {
        "summary": {
            "missing_records": missing_count,
            "removed_records": removed_count,
            "orphan_files": len(orphan_files)
        },
        "missing_records": [
            {
                "file": rec.get(COLUMN_FILENAME, ""),
                "path": rec.get(COLUMN_PATH, "")
            }
            for rec in missing_records
        ],
        "orphan_files": orphan_files
    }

    ensure_directory(report_dir)
    report_path = os.path.join(report_dir, f"CleanupMediaDatabaseReport.{report_format}")
    if report_format == "csv":
        rows = []
        for rec in report_data["missing_records"]:
            rows.append({"type": "missing_record", "path": rec["path"], "file": rec["file"]})
        for path in orphan_files:
            rows.append({"type": "orphan_file", "path": path, "file": ""})
        save_csv(rows, report_path, ["type", "path", "file"])
    else:
        save_json(report_data, report_path)
    logging.info("Report saved to %s", report_path)


if __name__ == "__main__":
    raise SystemExit(main())
