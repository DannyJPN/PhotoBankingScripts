import os
import pandas as pd
import logging
from colorlog import ColoredFormatter
from tqdm import tqdm
from datetime import datetime
import shutil
import sys
import csv
import chardet
import argparse

# Constants for statuses
STATUS_READY = "připraveno"
STATUS_CHECKED = "kontrolováno"

# Function to get the script name dynamically
def get_script_name():
    return os.path.splitext(os.path.basename(__file__))[0]

# Function to create sanitized log filename
def get_log_filename(log_dir):
    script_name = get_script_name()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{log_dir}/{script_name}_Log_{current_time}.log"

# Configure Logging
def configure_logging(log_dir, debug):
    # Ensure log directory exists
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = get_log_filename(log_dir)
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level,
                        format='%(log_color)s%(levelname)s:%(name)s:%(message)s',
                        handlers=[
                            logging.FileHandler(log_filename),
                            logging.StreamHandler()
                        ])

    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)s:%(name)s:%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'bold_white',
            'INFO': 'bold_green',
            'WARNING': 'bold_yellow',
            'ERROR': 'bold_red',
            'CRITICAL': 'bold_purple',
        },
        secondary_log_colors={},
        style='%'
    )

    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setFormatter(formatter)

# Function to detect encoding of a file
def detect_encoding(filepath):
    with open(filepath, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

# Function to load CSV file
def load_csv(filepath):
    try:
        encoding = detect_encoding(filepath)
        logging.info(f"Detected encoding: {encoding}")

        # Load CSV with na_filter=False to prevent NaN values
        df = pd.read_csv(filepath, na_filter=False, encoding=encoding)
        logging.info(f"CSV file loaded successfully: {filepath}")
        media_items = df.to_dict(orient='records')

        # Log first few media items for verification
        logging.debug(f"First few media items: {media_items[:5]}")

        return media_items, encoding
    except Exception as e:
        logging.error(f"Error loading CSV file: {e}", exc_info=True)
        sys.exit(1)

# Function to mark files as checked
def mark_files_as_checked(csv_data):
    try:
        logging.info("Marking files as checked")
        for row in tqdm(csv_data, desc="Processing rows"):
            for key in row.keys():
                if row[key] == STATUS_READY:
                    row[key] = STATUS_CHECKED
                    logging.debug(f"Replaced '{STATUS_READY}' with '{STATUS_CHECKED}' in row with data: {row}")
        logging.info("Files marked as checked successfully")
        return csv_data
    except Exception as e:
        logging.error(f"Failed to mark files as checked: {e}", exc_info=True)
        raise

# Function to save CSV file with backup
def save_csv(csv_data, filepath, encoding):
    try:
        # Create a backup of the original file
        backup_filepath = f"{filepath}.{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.old"
        shutil.copy(filepath, backup_filepath)
        logging.info(f"Backup of the original file created: {backup_filepath}")

        # Convert the list of dictionaries back to a DataFrame
        df = pd.DataFrame(csv_data)

        # Save the updated DataFrame to the original file path with all fields enclosed in double quotes
        df.to_csv(filepath, index=False, quotechar='"', quoting=csv.QUOTE_ALL, encoding=encoding)
        logging.info(f"CSV file saved successfully: {filepath}")
    except Exception as e:
        logging.error(f"Error saving CSV file: {e}", exc_info=True)
        sys.exit(1)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Mark media files as checked in a CSV file.")
    parser.add_argument("--PhotoCsvFile", type=str, default=r"F:\Disk Google (krupadan.jp@gmail.com)\XLS\Fotobanky/PhotoMediaTest.csv", help="Path to the photo CSV file.")
    parser.add_argument("--LogFile", type=str, default=r"H:/Logs", help="Directory for log files.")
    parser.add_argument("--debug", action='store_true', help="Enable debug level logging.")
    return parser.parse_args()

# Main script flow
def main():
    args = parse_arguments()

    # Update constants based on arguments
    PHOTO_CSV_FILE = args.PhotoCsvFile
    LOG_DIR = args.LogFile
    DEBUG_MODE = args.debug

    # Configure logging with the provided log directory and debug mode
    configure_logging(LOG_DIR, DEBUG_MODE)

    logging.info("Starting CSV processing with progress bar")
    csv_data, encoding = load_csv(PHOTO_CSV_FILE)
    updated_csv_data = mark_files_as_checked(csv_data)
    save_csv(updated_csv_data, PHOTO_CSV_FILE, encoding)
    logging.info("CSV processing completed successfully")

if __name__ == "__main__":
    main()