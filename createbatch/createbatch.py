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
    DEFAULT_EXIF_FOLDER,
    DEFAULT_LOG_DIR,
    STATUS_FIELD_KEYWORD,
    PREPARED_STATUS_VALUE
)
from createbatchlib.filtering import filter_prepared_media
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
        "--exif_tool_folder",
        type=str,
        default=DEFAULT_EXIF_FOLDER,
        help="Folder where the EXIF tool is located"
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
    return parser.parse_args()


def main():
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    # Ensure ExifTool availability
    args.exif_tool_folder = ensure_exiftool(args.exif_tool_folder)
    logging.debug("EXIF: %s", args.exif_tool_folder)
    logging.info("Starting CreateBatch process")

    # Load and filter records
    records: List[Dict[str, str]] = load_csv(args.photo_csv)
    prepared = filter_prepared_media(records)
    if not prepared:
        logging.warning("No prepared media records found. Exiting.")
        return

    # Identify unique photobanks
    banks = sorted({
        key[:key.lower().find(STATUS_FIELD_KEYWORD)].strip()
        for rec in prepared
        for key, val in rec.items()
        if STATUS_FIELD_KEYWORD in key.lower() and isinstance(val, str) and PREPARED_STATUS_VALUE.lower() in val.lower()
    })

    all_processed: List[str] = []
    # Process per photobank with individual progress bars
    for bank in banks:
        logging.info("Processing %d records for %s",
                     sum(1 for rec in prepared if any(
                         STATUS_FIELD_KEYWORD in k.lower()
                         and k[:k.lower().find(STATUS_FIELD_KEYWORD)].strip() == bank
                         and PREPARED_STATUS_VALUE.lower() in v.lower()
                         for k, v in rec.items()
                     )), bank)
        processed = []
        # Filter records for this bank
        bank_records = [
            rec for rec in prepared
            if any(
                STATUS_FIELD_KEYWORD in k.lower()
                and k[:k.lower().find(STATUS_FIELD_KEYWORD)].strip() == bank
                and PREPARED_STATUS_VALUE.lower() in v.lower()
                for k, v in rec.items()
            )
        ]
        for rec in tqdm(bank_records, desc=f"Preparing {bank}", unit="file"):
            try:
                paths = prepare_media_file(
                    rec,
                    args.output_folder,
                    args.exif_tool_folder,
                    overwrite=args.overwrite,
                    bank=bank
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