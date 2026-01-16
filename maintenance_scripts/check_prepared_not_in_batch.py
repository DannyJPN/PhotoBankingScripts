#!/usr/bin/env python3
"""
Check for records with 'připraveno' status for old banks that are not in any batch.

Records with status 'připraveno' should either be:
1. Already uploaded (and in batch folders), or
2. Ready for upload (and should be in batch folders)

If they have 'připraveno' but are NOT in any batch folder, this may indicate:
- Files marked as prepared but never copied to batch
- Batch folders deleted but status not updated
- Logic error in batch creation

Usage:
    python maintenance_scripts/check_prepared_not_in_batch.py
"""
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "updatemediadatabase"))

from shared.file_operations import load_csv

# Old/existing photobanks (excluding new ones from Issue #116)
OLD_BANKS = [
    "ShutterStock",
    "AdobeStock",
    "Dreamstime",
    "DepositPhotos",
    "GettyImages",
    "Pond5",
    "Alamy",
    "123RF",
    "BigStockPhoto",
    "CanStockPhoto"
]

# Default paths
DEFAULT_MEDIA_CSV = "L:/Můj disk/XLS/Fotobanky/PhotoMedia.csv"
DEFAULT_BATCH_FOLDER = "L:/Můj disk/PhotoBankMedia"

STATUS_PREPARED = "připraveno"
COLUMN_FILENAME = "Soubor"


def get_bank_status_column(bank: str) -> str:
    """Get status column name for a bank."""
    return f"{bank} status"


def find_files_in_batch_folders(batch_folder: str, banks: List[str]) -> Dict[str, Set[str]]:
    """
    Find all files in batch folders for specified banks.

    Args:
        batch_folder: Root batch folder path
        banks: List of bank names to check

    Returns:
        Dictionary mapping bank name to set of filenames found in batch folders
    """
    bank_files: Dict[str, Set[str]] = {bank: set() for bank in banks}

    for bank in banks:
        bank_folder = Path(batch_folder) / bank
        if not bank_folder.exists():
            logging.warning(f"Batch folder does not exist for {bank}: {bank_folder}")
            continue

        # Recursively find all files in bank folder
        for file_path in bank_folder.rglob("*"):
            if file_path.is_file():
                bank_files[bank].add(file_path.name)

    return bank_files


def main() -> None:
    """Check for prepared records not in batch folders."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Load PhotoMedia.csv
    logging.info(f"Loading {DEFAULT_MEDIA_CSV}")
    records = load_csv(DEFAULT_MEDIA_CSV)
    logging.info(f"Loaded {len(records)} records")

    # Find files in batch folders
    logging.info(f"Scanning batch folders in {DEFAULT_BATCH_FOLDER}")
    bank_files = find_files_in_batch_folders(DEFAULT_BATCH_FOLDER, OLD_BANKS)

    for bank, files in bank_files.items():
        logging.info(f"  {bank}: {len(files)} files in batch folders")

    # Check for records with 'připraveno' status not in batch
    logging.info("\nChecking for prepared records not in batch folders...")

    missing_records: Dict[str, List[Dict[str, str]]] = {bank: [] for bank in OLD_BANKS}

    for record in records:
        filename = record.get(COLUMN_FILENAME, "")
        if not filename:
            continue

        for bank in OLD_BANKS:
            status_col = get_bank_status_column(bank)
            status = record.get(status_col, "").strip().lower()

            if status == STATUS_PREPARED.lower():
                # Check if file is in batch folder
                if filename not in bank_files[bank]:
                    missing_records[bank].append(record)

    # Print results
    logging.info("\n" + "=" * 80)
    logging.info("RESULTS: Records with 'připraveno' status NOT in batch folders")
    logging.info("=" * 80)

    total_missing = 0
    for bank in OLD_BANKS:
        count = len(missing_records[bank])
        if count > 0:
            total_missing += count
            logging.info(f"\n{bank}: {count} records missing from batch")

            # Show first 5 examples
            for i, record in enumerate(missing_records[bank][:5]):
                logging.info(f"  Example {i+1}: {record.get(COLUMN_FILENAME, 'N/A')}")

            if count > 5:
                logging.info(f"  ... and {count - 5} more")

    if total_missing == 0:
        logging.info("\n✅ All records with 'připraveno' status are in batch folders!")
    else:
        logging.info(f"\n⚠️  Total missing: {total_missing} records across all banks")
        logging.info("\nPossible causes:")
        logging.info("  - Files marked as prepared but createbatch was never run")
        logging.info("  - Batch folders were deleted but status not updated")
        logging.info("  - Files filtered out during batch creation (editorial, size limits, etc.)")

    logging.info("=" * 80)


if __name__ == "__main__":
    main()