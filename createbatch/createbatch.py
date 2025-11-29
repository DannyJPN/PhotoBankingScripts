import os
import logging
from argparse import ArgumentParser
from typing import List, Dict
from collections import defaultdict

from shared.utils import get_log_filename
from shared.logging_config import setup_logging
from shared.file_operations import ensure_directory, load_csv
from shared.exif_downloader import ensure_exiftool
from createbatchlib.constants import (
    DEFAULT_PHOTO_CSV_FILE,
    DEFAULT_PROCESSED_MEDIA_FOLDER,
    DEFAULT_LOG_DIR,
    STATUS_FIELD_KEYWORD,
    PREPARED_STATUS_VALUE
)
from createbatchlib.filtering import filter_prepared_media
from createbatchlib.preparation import prepare_media_file
from createbatchlib.progress_tracker import UnifiedProgressTracker

def parse_arguments():
    parser = ArgumentParser(description="CreateBatch Script")
    parser.add_argument(
        "--photo_csv",
        type=str,
        default=DEFAULT_PHOTO_CSV_FILE,
        help="Path to CSV file with photo metadata"
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        default=DEFAULT_PROCESSED_MEDIA_FOLDER,
        help="Root folder where processed media will be placed"
    )
    parser.add_argument(
        "--overwrite",
        action='store_true',
        help="Overwrite existing files in the output folders"
    )
    parser.add_argument(
        "--log_dir",
        type=str,
        default=DEFAULT_LOG_DIR,
        help="Directory for log files"
    )
    parser.add_argument(
        "--debug",
        action='store_true',
        help="Enable debug logging"
    )
    parser.add_argument(
        "--include-edited",
        action='store_true',
        help="Include edited/processed photos from 'Upravené foto' folders (default: only original photos)"
    )
    parser.add_argument(
        "--include-alternative-formats",
        action='store_true',
        help="Include alternative formats (PNG, TIFF, RAW) in batch creation (default: only JPG)"
    )
    return parser.parse_args()


def group_records_by_bank(prepared_records: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """
    Group prepared records by bank (optimized single-pass).

    Args:
        prepared_records: List of records with PREPARED status

    Returns:
        Dictionary mapping bank name to list of records for that bank
    """
    bank_records = defaultdict(list)

    for record in prepared_records:
        record_banks = set()  # Track banks for this record to avoid duplicates

        for key, value in record.items():
            if (STATUS_FIELD_KEYWORD in key.lower() and
                isinstance(value, str) and
                PREPARED_STATUS_VALUE.lower() in value.lower()):

                bank_name = key[:key.lower().find(STATUS_FIELD_KEYWORD)].strip()
                if bank_name and bank_name not in record_banks:
                    bank_records[bank_name].append(record)
                    record_banks.add(bank_name)

    return dict(bank_records)


def main():
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    # Ensure ExifTool availability
    exif_tool_path = ensure_exiftool()
    logging.debug("EXIF: %s", exif_tool_path)
    logging.info("Starting CreateBatch process")

    # Load and filter records (no progress bar - fast operation)
    records: List[Dict[str, str]] = load_csv(args.photo_csv)
    prepared = filter_prepared_media(records, include_edited=args.include_edited)
    if not prepared:
        logging.warning("No prepared media records found. Exiting.")
        return

    # Group records by bank (single pass - optimized)
    bank_records_map = group_records_by_bank(prepared)
    banks = sorted(bank_records_map.keys())

    if not banks:
        logging.warning("No banks found in prepared records. Exiting.")
        return

    # Calculate records per bank for progress tracking
    records_per_bank = {bank: len(records) for bank, records in bank_records_map.items()}

    # Initialize unified progress tracker
    progress_tracker = UnifiedProgressTracker(banks, records_per_bank)

    all_processed: List[str] = []
    success_count = 0
    error_count = 0

    try:
        # Process each bank with unified progress tracking
        for bank in banks:
            bank_records = bank_records_map[bank]
            progress_tracker.start_bank(bank)

            processed = []
            bank_errors = 0

            for rec in bank_records:
                try:
                    paths = prepare_media_file(
                        rec,
                        args.output_folder,
                        exif_tool_path,
                        overwrite=args.overwrite,
                        bank=bank,
                        include_alternative_formats=args.include_alternative_formats
                    )
                    processed.extend(paths)
                    success_count += len(paths)
                    progress_tracker.update_progress(len(paths))

                except Exception as e:
                    logging.error(
                        "Error preparing file %s for %s: %s",
                        rec.get('Cesta'), bank, e
                    )
                    bank_errors += 1
                    error_count += 1
                    # Still update progress to keep bar moving
                    progress_tracker.update_progress(0)

            progress_tracker.finish_bank()
            all_processed.extend(processed)

            # Log bank completion summary
            logging.info(
                f"Completed {bank}: {len(processed)} files processed successfully, {bank_errors} errors"
            )

    finally:
        progress_tracker.finish_all()

    # Final summary
    if all_processed or error_count > 0:
        logging.info("=" * 60)
        logging.info("Processing summary:")
        logging.info(f"  Total files processed successfully: {len(all_processed)}")
        logging.info(f"  Total errors: {error_count}")
        logging.info(f"  Banks processed: {len(banks)}")
        if len(all_processed) + error_count > 0:
            success_rate = (len(all_processed) / (len(all_processed) + error_count)) * 100
            logging.info(f"  Success rate: {success_rate:.1f}%")
        logging.info("=" * 60)

    logging.info("CreateBatch process completed")

if __name__ == "__main__":
    main()