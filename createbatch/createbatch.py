import os
import logging
from argparse import ArgumentParser
from tqdm import tqdm
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
    PREPARED_STATUS_VALUE
)
from createbatchlib.optimization import RecordProcessor
from createbatchlib.preparation import prepare_media_file

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

    all_processed: List[str] = []
    # Process per photobank with individual progress bars
    for bank, bank_records in bank_records_map.items():
        logging.info("Processing %d records for %s", len(bank_records), bank)
        processed = []
        for rec in tqdm(bank_records, desc=f"Preparing {bank}", unit="file"):
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
            except Exception as e:
                logging.error(
                    "Error preparing file %s for %s: %s",
                    rec.get('Cesta'), bank, e
                )
        all_processed.extend(processed)

    # Summary of processed files
    if all_processed:
        logging.info("Processed total %d files:", len(all_processed))
        for path in all_processed:
            logging.info(" - %s", path)

    logging.info("CreateBatch process completed")

if __name__ == "__main__":
    main()