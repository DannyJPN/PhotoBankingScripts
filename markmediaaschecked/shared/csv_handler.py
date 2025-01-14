import pandas as pd
import logging
from datetime import datetime
import shutil
import csv
import sys
from shared.utils import detect_encoding

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