#!/usr/bin/env python3
"""
Check for records with 'připraveno' status that were NOT processed in any givenew batch.

These records may have incorrect status (leftover from previous processing).

Usage:
    python updatemediadatabase/check_prepared_without_batch.py
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

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
GIVENEW_BATCH_STATE = "F:/Dropbox/Scripts/Python/Fotobanking/givephotobankreadymediafiles/batch_state"

STATUS_PREPARED = "připraveno"
COLUMN_FILENAME = "Soubor"
COLUMN_TITLE = "Název"
COLUMN_DESCRIPTION = "Popis"
COLUMN_KEYWORDS = "Klíčová slova"


def get_bank_status_column(bank: str) -> str:
    """Get status column name for a bank."""
    return f"{bank} status"


def load_processed_files_from_batches(batch_state_dir: str) -> Set[str]:
    """
    Load all filenames that were processed in givenew batches.

    Args:
        batch_state_dir: Path to givenew batch_state directory

    Returns:
        Set of filenames (basenames) that were processed
    """
    processed_files = set()
    batches_dir = Path(batch_state_dir) / "batches"

    if not batches_dir.exists():
        logging.error(f"Batches directory does not exist: {batches_dir}")
        return processed_files

    # Iterate through all batch folders
    for batch_folder in batches_dir.iterdir():
        if not batch_folder.is_dir():
            continue

        state_file = batch_folder / "state.json"
        if not state_file.exists():
            continue

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            files = state.get("files", [])
            for file_entry in files:
                file_path = file_entry.get("file_path", "")
                if file_path:
                    filename = os.path.basename(file_path)
                    processed_files.add(filename)

        except Exception as e:
            logging.warning(f"Failed to read {state_file}: {e}")

    return processed_files


def has_metadata(record: Dict[str, str]) -> bool:
    """Check if record has complete metadata."""
    title = record.get(COLUMN_TITLE, "").strip()
    description = record.get(COLUMN_DESCRIPTION, "").strip()
    keywords = record.get(COLUMN_KEYWORDS, "").strip()
    return bool(title or description or keywords)


def is_edited_file(filename: str) -> bool:
    """Check if filename is an edited version (not original)."""
    edit_tags = ["_bw", "_negative", "_sharpen", "_misty", "_blurred"]
    filename_lower = filename.lower()
    for tag in edit_tags:
        if tag in filename_lower:
            return True
    return False


def main() -> None:
    """Check for prepared records not processed in batches."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Load processed files from givenew batches
    logging.info(f"Loading processed files from {GIVENEW_BATCH_STATE}")
    processed_files = load_processed_files_from_batches(GIVENEW_BATCH_STATE)
    logging.info(f"Found {len(processed_files)} files processed in batches")

    # Load PhotoMedia.csv
    logging.info(f"Loading {DEFAULT_MEDIA_CSV}")
    records = load_csv(DEFAULT_MEDIA_CSV)
    logging.info(f"Loaded {len(records)} records")

    # Check for records with 'připraveno' status not in batches
    logging.info("\nChecking for prepared records NOT processed in batches...")

    suspicious_records: Dict[str, List[Dict[str, str]]] = {bank: [] for bank in OLD_BANKS}

    for record in records:
        filename = record.get(COLUMN_FILENAME, "")
        if not filename:
            continue

        # Skip edited files - we only care about originals
        if is_edited_file(filename):
            continue

        # Check if file was processed in batch
        was_processed_in_batch = filename in processed_files

        for bank in OLD_BANKS:
            status_col = get_bank_status_column(bank)
            status = record.get(status_col, "").strip().lower()

            if status == STATUS_PREPARED.lower():
                # File has 'připraveno' status
                if not was_processed_in_batch:
                    # But was NOT processed in any batch - suspicious!
                    suspicious_records[bank].append(record)

    # Print results
    logging.info("\n" + "=" * 80)
    logging.info("RESULTS: ORIGINAL files with 'připraveno' NOT processed in givenew batches")
    logging.info("(Edited files like _bw, _negative, etc. are excluded)")
    logging.info("=" * 80)

    total_suspicious = 0
    for bank in OLD_BANKS:
        count = len(suspicious_records[bank])
        if count > 0:
            total_suspicious += count
            logging.info(f"\n{bank}: {count} suspicious records")

            # Show first 5 examples with metadata status
            for i, record in enumerate(suspicious_records[bank][:5]):
                has_meta = has_metadata(record)
                meta_status = "HAS metadata" if has_meta else "NO metadata"
                logging.info(f"  Example {i+1}: {record.get(COLUMN_FILENAME, 'N/A')} ({meta_status})")

            if count > 5:
                logging.info(f"  ... and {count - 5} more")

    if total_suspicious == 0:
        logging.info("\n✅ All records with 'připraveno' were processed in batches!")
    else:
        logging.info(f"\n⚠️  Total suspicious: {total_suspicious} records across all banks")
        logging.info("\nThese records have 'připraveno' status but were NOT processed in batches.")
        logging.info("Possible causes:")
        logging.info("  - Status was manually set to 'připraveno'")
        logging.info("  - Status was incorrectly migrated from old system")
        logging.info("  - Files were processed before batch tracking was implemented")
        logging.info("\nRecommended action:")
        logging.info("  - Review these records manually")
        logging.info("  - Verify if they have valid metadata")
        logging.info("  - Consider changing status if metadata is missing or incorrect")

    logging.info("=" * 80)


if __name__ == "__main__":
    main()