import pandas as pd
import logging
from datetime import datetime
import shutil
import csv
import sys
import os
from shared.utils import detect_encoding
from exportpreparedmedialib.export_objects import (
    ShutterStockExport,
    AdobeStockExport,
    DreamstimeExport,
    DepositPhotosExport,
    BigStockPhotoExport,
    RF123Export,
    CanStockPhotoExport,
    Pond5Export,
    AlamyExport,
    GettyImagesExport
)
from exportpreparedmedialib.header_mappings import HEADER_MAPPINGS
from exportpreparedmedialib.constants import DELIMITERS

def load_csv(filepath):
    try:
        encoding = detect_encoding(filepath)
        logging.info(f"Detected encoding: {encoding}")

        df = pd.read_csv(filepath, na_filter=False, encoding=encoding)
        logging.info(f"CSV file loaded successfully: {filepath}")
        media_items = df.to_dict(orient='records')

        logging.debug(f"First few media items: {media_items[:5]}")
        return media_items, encoding
    except Exception as e:
        logging.error(f"Error loading CSV file: {e}", exc_info=True)
        sys.exit(1)

def save_csv(csv_data, filepath, encoding):
    try:
        backup_filepath = f"{filepath}.{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv_old"
        shutil.copy(filepath, backup_filepath)
        logging.info(f"Backup of the original file created: {backup_filepath}")

        df = pd.DataFrame(csv_data)
        df.to_csv(filepath, index=False, quotechar='"', quoting=csv.QUOTE_ALL, encoding=encoding)
        logging.info(f"CSV file saved successfully: {filepath}")
    except Exception as e:
        logging.error(f"Error saving CSV file: {e}", exc_info=True)
        sys.exit(1)

def save_export_objects_to_csv(export_objects, photobank, csv_location):
    """Save a list of export objects to a CSV file."""
    try:
        # Define the CSV filename
        csv_filename = f"Csv_{photobank}.csv"
        filepath = os.path.join(csv_location, csv_filename)

        # Get the field names from the first export object
        if not export_objects:
            logging.warning(f"No export objects to save for {photobank}")
            return

        logging.debug(f"Processing {len(export_objects)} export objects for {photobank}")

        # Convert export objects to dictionaries
        rows = [obj.to_dict() for obj in export_objects]


        delimiter = DELIMITERS.get(photobank, DELIMITERS["default"])
        logging.debug(f"Using delimiter '{delimiter}' for {photobank}")

        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Write to CSV
        df = pd.DataFrame(rows)
        df.to_csv(filepath,
                 index=False,
                 sep=delimiter,
                 quoting=csv.QUOTE_ALL,
                 encoding='utf-8',
                 escapechar='\\',
                 na_rep='',
                 mode='a',  # Append mode
                 header=not os.path.exists(filepath))  # Write header only if the file doesn't exist

        logging.debug(f"Successfully saved {len(export_objects)} items to {filepath}")
        logging.debug(f"CSV file contents preview: {df.head()}")

    except Exception as e:
        logging.error(f"Error saving export objects to CSV for {photobank}: {e}", exc_info=True)
        raise

def initialize_csv_file(photobank, csv_location):
    """Initialize the CSV file with the header for a given photobank."""
    try:
        # Define the CSV filename
        csv_filename = f"Csv_{photobank}.csv"
        filepath = os.path.join(csv_location, csv_filename)

        # Get the header mapping for the photobank
        header_mapping = HEADER_MAPPINGS.get(photobank, {})
        headers = list(header_mapping.keys())
        delimiter = DELIMITERS.get(photobank, DELIMITERS["default"])
        # Write the header to the CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, quoting=csv.QUOTE_ALL,delimiter=delimiter)
            writer.writeheader()

        logging.info(f"Initialized CSV file with header {headers} for {photobank}: {filepath}")

    except Exception as e:
        logging.error(f"Error initializing CSV file for {photobank}: {e}", exc_info=True)
        raise