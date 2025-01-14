import os
import sys
import argparse
import logging
from shared.logging_config import setup_logging
from shared.csv_handler import load_csv, save_csv
from markmediaascheckedlib.mark_files import mark_files_as_checked
from markmediaascheckedlib.constants import PHOTO_CSV_FILE_DEFAULT, LOG_DIR
from shared.utils import get_log_filename

def parse_arguments():
    parser = argparse.ArgumentParser(description="Mark media files as checked in a CSV file.")
    parser.add_argument("--PhotoCsvFile", type=str, default=PHOTO_CSV_FILE_DEFAULT, help="Path to the photo CSV file.")
    parser.add_argument("--Debug", action='store_true', help="Enable debug level logging.")
    return parser.parse_args()

def main():
    args = parse_arguments()

    PHOTO_CSV_FILE = args.PhotoCsvFile

    # Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Generate the log filename
    LOG_FILE = get_log_filename(LOG_DIR)

    # Setup logging with the log file path
    setup_logging(args.Debug, LOG_FILE)

    logging.info("Starting CSV processing with progress bar")
    try:
        csv_data, encoding = load_csv(PHOTO_CSV_FILE)
        updated_csv_data = mark_files_as_checked(csv_data)
        save_csv(updated_csv_data, PHOTO_CSV_FILE, encoding)
        logging.info("CSV processing completed successfully")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()