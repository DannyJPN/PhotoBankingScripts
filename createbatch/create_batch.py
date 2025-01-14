import os
import sys
import logging
import argparse
from datetime import datetime
from createbatchlib.ensure_directories import ensure_directories
from createbatchlib.load_csv import load_csv
from createbatchlib.get_prepared_media_items import get_prepared_media_items
from createbatchlib.copy_media_items_to_batch import copy_media_items_to_batch
from createbatchlib.update_exif_data import update_exif_data
from shared.logging_config import setup_logging
from createbatchlib.constants import DEFAULT_PHOTO_CSV_FILE, DEFAULT_PROCESSED_MEDIA_FOLDER, DEFAULT_EXIF_TOOL_FOLDER, LOG_DIR
from tqdm import tqdm  # Ensure TQDM is imported
from shared.utils import get_log_filename

def parse_arguments():
    parser = argparse.ArgumentParser(description="CreateBatch Script")
    parser.add_argument("--PhotoCsvFile", type=str, default=DEFAULT_PHOTO_CSV_FILE)
    parser.add_argument("--ProcessedMediaFolder", type=str, default=DEFAULT_PROCESSED_MEDIA_FOLDER)
    parser.add_argument("--ExifToolFolder", type=str, default=DEFAULT_EXIF_TOOL_FOLDER)
    parser.add_argument("--Debug", action="store_true")

    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()
    
    # Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Generate the log filename
    LOG_FILE = get_log_filename(LOG_DIR)

    # Setup logging with the log file path
    setup_logging(args.Debug, LOG_FILE)
    
    logging.info("Script started with the following parameters:")
    logging.info(f"PhotoCsvFile: {args.PhotoCsvFile}")
    logging.info(f"ProcessedMediaFolder: {args.ProcessedMediaFolder}")
    logging.info(f"LogFile: {LOG_FILE}")
    logging.info(f"ExifToolFolder: {args.ExifToolFolder}")
    logging.info(f"Debug: {args.Debug}")

    ensure_directories(args.ProcessedMediaFolder, os.path.dirname(LOG_FILE))
    logging.info("Necessary directories ensured.")

    media_items = load_csv(args.PhotoCsvFile)
    logging.info(f"Loaded {len(media_items)} media items from CSV.")

    prepared_media_items = get_prepared_media_items(media_items)

    updated_media_items = copy_media_items_to_batch(prepared_media_items, args.ProcessedMediaFolder)

    update_exif_data(updated_media_items, args.ExifToolFolder)

    scripts = ["export_prepared_media.py", "mark_media_as_checked.py", "launch_photobanks.py"]
    for script in scripts:
        try:
            script_path = os.path.join(os.path.dirname(__file__), script)
            logging.info(f"Launching script: {script_path}")
            logging.info(f"Successfully launched script: {script_path}")
        except Exception as e:
            logging.error(f"Error launching script {script}: {e}", exc_info=True)

if __name__ == "__main__":
    main()