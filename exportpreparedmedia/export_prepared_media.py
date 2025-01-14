import os
import sys
import argparse
import logging
from tqdm import tqdm  # Import tqdm for progress bar
from shared.logging_config import setup_logging
from shared.csv_handler import load_csv
from exportpreparedmedialib.constants import PHOTO_CSV_FILE_DEFAULT, CSV_LOCATION_DEFAULT, LOG_DIR, STATUS_READY, CATEGORY_CSV_DIR, PHOTOBANKS
from shared.utils import get_log_filename
from shared.media_filter import filter_prepared_items
from exportpreparedmedialib.category_handler import load_all_categories
from exportpreparedmedialib.export_processor import process_exports

def parse_arguments():
    parser = argparse.ArgumentParser(description="Export prepared media files to photobank-specific CSV files.")
    parser.add_argument("--PhotoCsvFile", type=str, default=PHOTO_CSV_FILE_DEFAULT, help="Path to the photo CSV file.")
    parser.add_argument("--CsvLocation", type=str, default=CSV_LOCATION_DEFAULT, help="Path to the directory where generated CSV files will be saved.")
    parser.add_argument("--Debug", action='store_true', help="Enable debug level logging.")
    return parser.parse_args()

def main():
    args = parse_arguments()

    PHOTO_CSV_FILE = args.PhotoCsvFile
    CSV_LOCATION = args.CsvLocation

    # Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        logging.info(f"Created log directory: {LOG_DIR}")

    # Ensure the CSV output directory exists
    if not os.path.exists(CSV_LOCATION):
        os.makedirs(CSV_LOCATION)
        logging.info(f"Created CSV output directory: {CSV_LOCATION}")

    # Generate the log filename
    LOG_FILE = get_log_filename(LOG_DIR)

    # Setup logging with the log file path
    setup_logging(args.Debug, LOG_FILE)

    logging.info("Starting media export processing")
    try:
        # Load and validate input CSV file
        logging.info(f"Loading input CSV file: {PHOTO_CSV_FILE}")
        csv_data, encoding = load_csv(PHOTO_CSV_FILE)
        logging.info(f"Successfully loaded {len(csv_data)} items from CSV")

        # Filter media items with 'připraveno' status
        logging.info(f"Filtering items with '{STATUS_READY}' status")
        prepared_items = filter_prepared_items(csv_data, STATUS_READY)
        logging.info(f"Found {len(prepared_items)} items with '{STATUS_READY}' status")
        logging.debug(f"First 5 prepared items: {prepared_items[:5]}")

        # Load all categories
        logging.info(f"Loading category mappings from: {CATEGORY_CSV_DIR}")
        all_categories = load_all_categories(CATEGORY_CSV_DIR)
        logging.info("Successfully loaded category mappings")
        logging.debug(f"Category mappings: {all_categories}")

        # Process exports and generate CSV files
        logging.info("Starting export processing for each photobank")
        process_exports(prepared_items, PHOTOBANKS, all_categories, CSV_LOCATION)
        logging.info("Export processing completed successfully")

    except FileNotFoundError as e:
        logging.error(f"Required file not found: {e}", exc_info=True)
        sys.exit(1)
    except PermissionError as e:
        logging.error(f"Permission denied when accessing file: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()