#!/usr/bin/env python3
"""
Fix invalid 'připraveno' statuses for records without metadata.

Records with status 'připraveno' but missing metadata (title, description, keywords)
will have their status updated to:
- 'zamítnuto - velikost' if they don't meet photobank size limits
- 'nezpracováno' if they meet the limits

Usage:
    python maintenance_scripts/fix_invalid_prepared_statuses.py --dry-run
    python maintenance_scripts/fix_invalid_prepared_statuses.py
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add project root and updatemediadatabase to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "updatemediadatabase"))

from shared.file_operations import load_csv, save_csv_with_backup

from updatemedialdatabaselib.constants import (
    DEFAULT_MEDIA_CSV_PATH,
    DEFAULT_LIMITS_CSV_PATH,
    COLUMN_FILENAME,
    COLUMN_WIDTH,
    COLUMN_HEIGHT,
    COLUMN_RESOLUTION,
    COLUMN_TITLE,
    COLUMN_DESCRIPTION,
    COLUMN_KEYWORDS,
    STATUS_PREPARED,
    STATUS_UNPROCESSED,
    STATUS_REJECTED_SIZE
)
from updatemedialdatabaselib.photo_analyzer import validate_against_limits


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Fix invalid 'připraveno' statuses for records without metadata."
    )
    parser.add_argument("--media_csv", type=str, default=DEFAULT_MEDIA_CSV_PATH,
                        help="Path to PhotoMedia.csv")
    parser.add_argument("--limits_csv", type=str, default=DEFAULT_LIMITS_CSV_PATH,
                        help="Path to PhotoLimits.csv")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing the CSV")
    return parser.parse_args()


def has_metadata(record: Dict[str, str]) -> bool:
    """
    Check if record has complete metadata.

    Args:
        record: CSV record dictionary

    Returns:
        True if record has title, description, or keywords
    """
    title = record.get(COLUMN_TITLE, "").strip()
    description = record.get(COLUMN_DESCRIPTION, "").strip()
    keywords = record.get(COLUMN_KEYWORDS, "").strip()

    # Record has metadata if ANY of these fields is non-empty
    return bool(title or description or keywords)


def get_photobank_status_columns(record: Dict[str, str]) -> List[str]:
    """
    Get all photobank status column names from record.

    Args:
        record: CSV record dictionary

    Returns:
        List of column names that contain 'status'
    """
    return [col for col in record.keys() if 'status' in col.lower()]


def parse_dimensions(record: Dict[str, str]) -> Dict[str, object]:
    """
    Parse dimensions and resolution from record.

    Args:
        record: CSV record dictionary

    Returns:
        Metadata dict with Width, Height, Resolution
    """
    metadata: Dict[str, object] = {
        "Filename": record.get(COLUMN_FILENAME, "")
    }

    try:
        width = int(record.get(COLUMN_WIDTH, "0") or "0")
        if width > 0:
            metadata["Width"] = width
    except ValueError:
        pass

    try:
        height = int(record.get(COLUMN_HEIGHT, "0") or "0")
        if height > 0:
            metadata["Height"] = height
    except ValueError:
        pass

    resolution = record.get(COLUMN_RESOLUTION, "").strip()
    if resolution:
        metadata["Resolution"] = resolution

    return metadata


def main() -> None:
    """Fix invalid prepared statuses."""
    args = parse_arguments()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Load CSV files
    records = load_csv(args.media_csv)
    limits = load_csv(args.limits_csv)

    logging.info(f"Loaded {len(records)} records from {args.media_csv}")
    logging.info(f"Loaded {len(limits)} photobank limits from {args.limits_csv}")

    # Track statistics
    scanned = 0
    invalid_statuses_found = 0
    fixed_to_unprocessed = 0
    fixed_to_rejected_size = 0
    banks_fixed: Set[str] = set()

    for record in records:
        filename = record.get(COLUMN_FILENAME, "unknown")

        # Check if record has metadata
        if has_metadata(record):
            continue  # Has metadata, status is valid

        # Get all status columns
        status_columns = get_photobank_status_columns(record)

        # Check each status column for 'připraveno'
        has_invalid_status = False
        for status_col in status_columns:
            if record.get(status_col, "").strip().lower() == STATUS_PREPARED.lower():
                has_invalid_status = True
                break

        if not has_invalid_status:
            continue  # No 'připraveno' status found

        # Found invalid status - record has 'připraveno' but no metadata
        scanned += 1
        invalid_statuses_found += 1

        if scanned <= 5:  # Show first 5 examples
            logging.info(f"Invalid status found: {filename} - has 'připraveno' but no metadata")

        # Parse dimensions for validation
        metadata = parse_dimensions(record)

        # Validate against limits for all banks
        validation_results = validate_against_limits(metadata, limits)

        # Fix status for each bank
        for status_col in status_columns:
            if record.get(status_col, "").strip().lower() != STATUS_PREPARED.lower():
                continue  # Not 'připraveno', skip

            # Extract bank name from status column (e.g., "AdobeStock status" -> "AdobeStock")
            bank_name = status_col.replace(" status", "").strip()

            # Check if bank accepts this file based on size limits
            is_valid = validation_results.get(bank_name, True)

            if is_valid:
                # Meets size limits -> 'nezpracováno'
                record[status_col] = STATUS_UNPROCESSED
                fixed_to_unprocessed += 1
                banks_fixed.add(bank_name)
            else:
                # Doesn't meet size limits -> 'zamítnuto - velikost'
                record[status_col] = STATUS_REJECTED_SIZE
                fixed_to_rejected_size += 1
                banks_fixed.add(bank_name)

    # Print summary
    logging.info("")
    logging.info("=" * 60)
    logging.info("Summary:")
    logging.info(f"  Records with invalid statuses: {invalid_statuses_found}")
    logging.info(f"  Status fields fixed to 'nezpracováno': {fixed_to_unprocessed}")
    logging.info(f"  Status fields fixed to 'zamítnuto - velikost': {fixed_to_rejected_size}")
    logging.info(f"  Total status fields fixed: {fixed_to_unprocessed + fixed_to_rejected_size}")
    logging.info(f"  Banks affected: {', '.join(sorted(banks_fixed))}")
    logging.info("=" * 60)

    if args.dry_run:
        logging.info("")
        logging.info("DRY RUN - No changes written to disk")
        logging.info(f"Run without --dry-run to apply fixes to {args.media_csv}")
        return

    if invalid_statuses_found == 0:
        logging.info("No invalid statuses found - nothing to fix")
        return

    # Save updated CSV
    save_csv_with_backup(records, args.media_csv)
    logging.info(f"Updated {args.media_csv} with fixed statuses")


if __name__ == "__main__":
    main()