import os
import logging
from argparse import ArgumentParser
from typing import List, Dict

from shared.utils import get_log_filename
from shared.logging_config import setup_logging
from shared.file_operations import ensure_directory, load_csv
from shared.exif_downloader import ensure_exiftool
from createbatchlib.constants import (
    DEFAULT_PHOTO_CSV_FILE,
    DEFAULT_PROCESSED_MEDIA_FOLDER,
    DEFAULT_LOG_DIR,
    STATUS_FIELD_KEYWORD,
    PREPARED_STATUS_VALUE,
    PHOTOBANK_BATCH_SIZE_LIMITS
)
from createbatchlib.optimization import RecordProcessor
from createbatchlib.media_preparation import prepare_media_file, split_into_batches
from createbatchlib.progress_tracker import UnifiedProgressTracker
from createbatchlib.filtering import filter_editorial_for_bank

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

    # Load CSV and process with optimized single-pass algorithm
    records: List[Dict[str, str]] = load_csv(args.photo_csv)

    # Initialize optimized record processor
    processor = RecordProcessor(STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE)

    # Single-pass filtering and grouping by bank (O(n) instead of O(n²))
    bank_records_map = processor.process_records_optimized(
        records,
        include_edited=args.include_edited
    )

    if not bank_records_map:
        logging.warning("No prepared media records found. Exiting.")
        return

    # Calculate records per bank and get sorted bank list
    records_per_bank = {bank: len(records) for bank, records in bank_records_map.items()}
    banks = sorted(bank_records_map.keys())

    if not banks:
        logging.warning("No banks found in prepared records. Exiting.")
        return

    # Initialize unified progress tracker
    progress_tracker = UnifiedProgressTracker(banks, records_per_bank)

    all_processed: List[str] = []
    error_count = 0

    try:
        # Process each bank with unified progress tracking
        for bank in banks:
            bank_records = bank_records_map[bank]

            # Filter out editorial content for banks that don't accept it
            bank_records = filter_editorial_for_bank(bank_records, bank)

            if not bank_records:
                logging.info(f"No records to process for {bank} after editorial filtering, skipping")
                continue

            progress_tracker.start_bank(bank)

            processed = []
            bank_errors = 0

            # Check if bank has batch size limit
            batch_size_limit = PHOTOBANK_BATCH_SIZE_LIMITS.get(bank, 0)

            if batch_size_limit > 0:
                # Split into batches for banks with size limits
                batches = split_into_batches(bank_records, batch_size_limit)
                logging.info(f"{bank} has batch size limit of {batch_size_limit}, created {len(batches)} batches")
            else:
                # No splitting for banks without limits
                batches = [bank_records]

            # Process each batch
            for batch_idx, batch_records in enumerate(batches, start=1):
                batch_num = batch_idx if batch_size_limit > 0 else None

                for rec in batch_records:
                    try:
                        paths = prepare_media_file(
                            rec,
                            args.output_folder,
                            exif_tool_path,
                            overwrite=args.overwrite,
                            bank=bank,
                            include_alternative_formats=args.include_alternative_formats,
                            batch_number=batch_num
                        )
                        processed.extend(paths)
                        progress_tracker.update_progress(1)  # Track by record, not files

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