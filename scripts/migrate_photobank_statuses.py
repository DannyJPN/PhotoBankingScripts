"""
Migrate PhotoMedia.csv to add new photobanks and deprecate old ones.

This script adds columns for 7 new photobanks, migrates statuses for deprecated banks,
and applies conditional migration rules based on existing photobank statuses.

Usage:
    python scripts/migrate_photobank_statuses.py --dry-run  # Preview changes
    python scripts/migrate_photobank_statuses.py            # Apply migration
"""

import argparse
import csv
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


# New photobanks to add
NEW_BANKS = ["Pixta", "Freepik", "Vecteezy", "StoryBlocks", "Envato", "500px", "MostPhotos"]

# Existing photobanks (canonical names after normalization)
EXISTING_BANKS = [
    "ShutterStock",
    "AdobeStock",
    "Dreamstime",
    "DepositPhotos",
    "GettyImages",
    "Pond5",
    "Alamy",
    "123RF",
    "BigStockPhoto",
    "CanStockPhoto",
]

# Deprecated photobanks
DEPRECATED_BANKS = ["BigStockPhoto", "CanStockPhoto"]

# Video file extensions (for StoryBlocks special handling)
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.wmv', '.mkv'}

# Status constants
STATUS_UNPROCESSED = "nezpracováno"
STATUS_PREPARED = "připraveno"
STATUS_UNAVAILABLE = "nedostupné"


class MigrationReport:
    """Track migration statistics and changes."""

    def __init__(self) -> None:
        """Initialize empty report."""
        self.rows_processed = 0
        self.deprecated_migrations = 0
        self.new_bank_prepared = 0
        self.new_bank_unprocessed = 0
        self.storyblocks_unavailable = 0
        self.mostphotos_unavailable = 0

    def print_summary(self) -> None:
        """Print migration summary."""
        print(f"\n=== Migration Report ===")
        print(f"Total rows processed: {self.rows_processed}")
        print(f"\nDeprecated bank migrations:")
        print(f"  BigStockPhoto/CanStockPhoto 'nezpracováno' -> 'nedostupné': {self.deprecated_migrations}")
        print(f"\nNew bank status assignments:")
        print(f"  Set to 'připraveno' (has processed files): {self.new_bank_prepared}")
        print(f"  Set to 'nezpracováno' (no processed files): {self.new_bank_unprocessed}")
        print(f"\nSpecial cases:")
        print(f"  StoryBlocks 'nedostupné' (non-video files): {self.storyblocks_unavailable}")
        print(f"  MostPhotos 'nedostupné' (all files): {self.mostphotos_unavailable}")


def get_column_name(bank: str, column_type: str) -> str:
    """Get column name for a photobank.

    Args:
        bank: Photobank name
        column_type: Either 'status' or 'kategorie'

    Returns:
        Column name (e.g., "Pixta status" or "Pixta kategorie")
    """
    return f"{bank} {column_type}"


def is_video_file(file_path: str) -> bool:
    """Check if file is a video based on extension.

    Args:
        file_path: Path to media file

    Returns:
        True if file is a video
    """
    ext = Path(file_path).suffix.lower()
    return ext in VIDEO_EXTENSIONS


def has_any_unprocessed(row: Dict[str, str], existing_banks: List[str]) -> bool:
    """Check if row has any unprocessed status in existing banks.

    Args:
        row: CSV row as dictionary
        existing_banks: List of existing bank names

    Returns:
        True if ANY existing bank has status "nezpracováno"
    """
    for bank in existing_banks:
        status_col = get_column_name(bank, "status")
        if status_col in row and row[status_col] == STATUS_UNPROCESSED:
            return True
    return False


def migrate_row(row: Dict[str, str], report: MigrationReport) -> Dict[str, str]:
    """Migrate a single row with new photobank columns and updated statuses.

    Args:
        row: CSV row as dictionary
        report: Report object to track statistics

    Returns:
        Updated row with new columns and migrated statuses
    """
    # 1. Migrate deprecated banks
    for bank in DEPRECATED_BANKS:
        status_col = get_column_name(bank, "status")
        if row.get(status_col) == STATUS_UNPROCESSED:
            row[status_col] = STATUS_UNAVAILABLE
            report.deprecated_migrations += 1

    # 2. Determine if this file has any unprocessed status in existing banks
    # Exclude deprecated banks from this check
    active_existing_banks = [b for b in EXISTING_BANKS if b not in DEPRECATED_BANKS]
    has_unprocessed = has_any_unprocessed(row, active_existing_banks)

    # 3. Get file path for special handling
    file_path = row.get("Cesta", "")
    is_video = is_video_file(file_path)

    # 4. Add and populate new bank STATUS columns (all status together)
    for bank in NEW_BANKS:
        status_col = get_column_name(bank, "status")

        # Special case: StoryBlocks (video-only)
        if bank == "StoryBlocks":
            if is_video:
                # Apply normal rules for videos
                if has_unprocessed:
                    # Has "nezpracováno" somewhere → not fully processed
                    row[status_col] = STATUS_UNPROCESSED
                    report.new_bank_unprocessed += 1
                else:
                    # No "nezpracováno" anywhere → fully processed
                    row[status_col] = STATUS_PREPARED
                    report.new_bank_prepared += 1
            else:
                # Photos/vectors not supported
                row[status_col] = STATUS_UNAVAILABLE
                report.storyblocks_unavailable += 1

        # Special case: MostPhotos (disabled)
        elif bank == "MostPhotos":
            row[status_col] = STATUS_UNAVAILABLE
            report.mostphotos_unavailable += 1

        # Normal banks
        else:
            if has_unprocessed:
                # Has "nezpracováno" somewhere → not fully processed
                row[status_col] = STATUS_UNPROCESSED
                report.new_bank_unprocessed += 1
            else:
                # No "nezpracováno" anywhere → fully processed
                row[status_col] = STATUS_PREPARED
                report.new_bank_prepared += 1

    # 5. Add new bank KATEGORIE columns (all kategorie together)
    for bank in NEW_BANKS:
        category_col = get_column_name(bank, "kategorie")
        row[category_col] = ""

    report.rows_processed += 1
    return row


def migrate_photomedia_csv(csv_path: Path, dry_run: bool = True) -> None:
    """Migrate PhotoMedia.csv with new photobanks and updated statuses.

    Args:
        csv_path: Path to PhotoMedia.csv
        dry_run: If True, only preview changes without modifying file
    """
    if not csv_path.exists():
        print(f"Error: PhotoMedia.csv not found at {csv_path}")
        sys.exit(1)

    print(f"{'DRY RUN: ' if dry_run else ''}Migrating PhotoMedia.csv...")
    print(f"File: {csv_path}")

    # Create backup
    if not dry_run:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = csv_path.parent / f"PhotoMedia_backup_{timestamp}.csv"
        print(f"\nCreating backup: {backup_path}")
        shutil.copy2(csv_path, backup_path)

    # Read CSV
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            original_fieldnames = reader.fieldnames
            rows = list(reader)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    if not original_fieldnames:
        print("Error: CSV file has no headers")
        sys.exit(1)

    print(f"\nOriginal columns: {len(original_fieldnames)}")
    print(f"Rows to process: {len(rows)}")

    # Build new fieldnames (add new bank columns after existing bank columns)
    new_fieldnames = list(original_fieldnames)

    # Find insertion points BEFORE any modifications
    # 1. Find last STATUS column (should be "Pond5 status")
    last_status_col_index = -1
    for i, field in enumerate(original_fieldnames):
        if "status" in field.lower():
            last_status_col_index = i

    # 2. Find last KATEGORIE column (should be "Pond5 kategorie")
    last_kategorie_col_index = -1
    for i, field in enumerate(original_fieldnames):
        if "kategorie" in field.lower():
            last_kategorie_col_index = i

    if last_status_col_index == -1 or last_kategorie_col_index == -1:
        print("Error: Could not find status or kategorie columns")
        sys.exit(1)

    print(f"Insertion points: status after index {last_status_col_index} ({original_fieldnames[last_status_col_index]}), kategorie after index {last_kategorie_col_index} ({original_fieldnames[last_kategorie_col_index]})")

    # Insert new bank STATUS columns right after last existing STATUS column
    status_insert_index = last_status_col_index + 1
    for bank in NEW_BANKS:
        status_col = get_column_name(bank, "status")
        if status_col not in new_fieldnames:
            new_fieldnames.insert(status_insert_index, status_col)
            status_insert_index += 1
            # Adjust kategorie index because we inserted before it
            last_kategorie_col_index += 1

    # Insert new bank KATEGORIE columns right after last existing KATEGORIE column
    kategorie_insert_index = last_kategorie_col_index + 1
    for bank in NEW_BANKS:
        category_col = get_column_name(bank, "kategorie")
        if category_col not in new_fieldnames:
            new_fieldnames.insert(kategorie_insert_index, category_col)
            kategorie_insert_index += 1

    print(f"New columns: {len(new_fieldnames)} (+{len(new_fieldnames) - len(original_fieldnames)} added)")

    # Initialize report
    report = MigrationReport()

    # Migrate each row
    migrated_rows = []
    for row in rows:
        # Add empty values for new columns
        for field in new_fieldnames:
            if field not in row:
                row[field] = ""

        # Apply migration logic
        migrated_row = migrate_row(row, report)
        migrated_rows.append(migrated_row)

    # Print report
    report.print_summary()

    # Preview changes (dry-run)
    if dry_run:
        print(f"\n=== Sample of migrated data (first 3 rows) ===")
        for i, row in enumerate(migrated_rows[:3]):
            print(f"\nRow {i+1}:")
            print(f"  File: {row.get('Soubor', 'N/A')}")

            # Show deprecated bank changes
            for bank in DEPRECATED_BANKS:
                status_col = get_column_name(bank, "status")
                print(f"  {status_col}: {row.get(status_col, 'N/A')}")

            # Show new bank statuses
            for bank in NEW_BANKS:
                status_col = get_column_name(bank, "status")
                print(f"  {status_col}: {row.get(status_col, 'N/A')}")

        print(f"\n{'='*60}")
        print("This was a DRY RUN - no files were modified.")
        print("Run without --dry-run to apply migration.")
        print(f"{'='*60}")
        return

    # Write migrated data
    try:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(migrated_rows)

        print(f"\nMigration completed successfully!")
        print(f"Backup created: {backup_path}")

    except Exception as e:
        print(f"\nError writing CSV: {e}")
        print(f"Your data is safe - restore from backup: {backup_path}")
        sys.exit(1)


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        description="Migrate PhotoMedia.csv with new photobanks"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=Path(r"L:\Můj disk\XLS\Fotobanky\PhotoMedia.csv"),
        help="Path to PhotoMedia.csv (default: L:\\Můj disk\\XLS\\Fotobanky\\PhotoMedia.csv)"
    )

    args = parser.parse_args()

    try:
        migrate_photomedia_csv(args.csv_path, dry_run=args.dry_run)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())