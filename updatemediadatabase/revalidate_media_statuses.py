#!/usr/bin/env python3
"""
Revalidate PhotoMedia.csv statuses for video and vector records using PhotoLimits.csv.

Usage:
    python updatemediadatabase/revalidate_media_statuses.py --media_csv PATH --limits_csv PATH
    python updatemediadatabase/revalidate_media_statuses.py --dry-run
"""
import argparse
import logging
import os
from typing import Dict, List

from shared.file_operations import load_csv, save_csv_with_backup

from updatemedialdatabaselib.constants import (
    DEFAULT_MEDIA_CSV_PATH,
    DEFAULT_LIMITS_CSV_PATH,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    VECTOR_EXTENSIONS,
    TYPE_PHOTO,
    TYPE_VIDEO,
    TYPE_VECTOR,
    COLUMN_FILENAME,
    COLUMN_PATH,
    COLUMN_WIDTH,
    COLUMN_HEIGHT,
    COLUMN_RESOLUTION
)
from updatemedialdatabaselib.media_processor import get_bank_status
from updatemedialdatabaselib.photo_analyzer import validate_against_limits


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Revalidate statuses for video/vector records in PhotoMedia.csv."
    )
    parser.add_argument("--media_csv", type=str, default=DEFAULT_MEDIA_CSV_PATH,
                        help="Path to PhotoMedia.csv")
    parser.add_argument("--limits_csv", type=str, default=DEFAULT_LIMITS_CSV_PATH,
                        help="Path to PhotoLimits.csv")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing the CSV")
    return parser.parse_args()


def infer_media_type(path_value: str, filename: str) -> str:
    """Infer media type from path or filename extension."""
    candidate = path_value or filename
    ext = os.path.splitext(candidate)[1].lower()
    if ext in VIDEO_EXTENSIONS:
        return TYPE_VIDEO
    if ext in VECTOR_EXTENSIONS:
        return TYPE_VECTOR
    if ext in IMAGE_EXTENSIONS:
        return TYPE_PHOTO
    return ""


def parse_int(value: str) -> int | None:
    """Parse integer from CSV field, returning None if invalid."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_metadata(record: Dict[str, str], media_type: str) -> Dict[str, object]:
    """Build metadata dict for limit validation from CSV record."""
    metadata: Dict[str, object] = {
        "Type": media_type,
        "Filename": record.get(COLUMN_FILENAME, ""),
        "Path": record.get(COLUMN_PATH, ""),
    }
    width = parse_int(record.get(COLUMN_WIDTH, ""))
    height = parse_int(record.get(COLUMN_HEIGHT, ""))
    if width is not None:
        metadata["Width"] = width
    if height is not None:
        metadata["Height"] = height
    resolution = record.get(COLUMN_RESOLUTION, "")
    if resolution:
        metadata["Resolution"] = resolution
    return metadata


def update_record_statuses(
    record: Dict[str, str],
    limits: List[Dict[str, str]],
    media_type: str
) -> bool:
    """Update status fields in record. Returns True if any status changed."""
    metadata = build_metadata(record, media_type)
    results = validate_against_limits(metadata, limits)
    changed = False
    for bank_name, is_valid in results.items():
        status_column = f"{bank_name} status"
        if status_column not in record:
            continue
        new_status = get_bank_status(bank_name, is_valid, metadata)
        if record.get(status_column) != new_status:
            record[status_column] = new_status
            changed = True
    return changed


def main() -> None:
    """Run status revalidation for video and vector records."""
    args = parse_arguments()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    records = load_csv(args.media_csv)
    limits = load_csv(args.limits_csv)

    updated = 0
    scanned = 0
    for record in records:
        media_type = infer_media_type(record.get(COLUMN_PATH, ""), record.get(COLUMN_FILENAME, ""))
        if media_type not in [TYPE_VIDEO, TYPE_VECTOR]:
            continue
        scanned += 1
        if update_record_statuses(record, limits, media_type):
            updated += 1

    logging.info("Scanned %d video/vector records, updated %d", scanned, updated)

    if args.dry_run:
        logging.info("Dry-run enabled; no changes written.")
        return

    if updated:
        save_csv_with_backup(records, args.media_csv)
        logging.info("Updated PhotoMedia.csv saved.")
    else:
        logging.info("No changes to save.")


if __name__ == "__main__":
    main()
