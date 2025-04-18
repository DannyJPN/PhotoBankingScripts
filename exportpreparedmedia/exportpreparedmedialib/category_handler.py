import os
import pandas as pd
import logging
import csv
from shared.utils import detect_encoding
from exportpreparedmedialib.constants import CATEGORY_CSV_DIR, CSV_LOCATION_DEFAULT, PHOTOBANK_HEADERS, PHOTOBANKS

def load_category_csv(filepath):
    """Load a category CSV file and return a dictionary mapping category names to their values."""
    try:
        logging.debug(f"Loading categories from file: {filepath}")
        encoding = detect_encoding(filepath)
        df = pd.read_csv(filepath, na_filter=False, encoding=encoding)

        # Log the columns of the DataFrame
        logging.debug(f"Columns in {filepath}: {df.columns.tolist()}")
        # Log the first few rows of the DataFrame
        logging.debug(f"First few rows in {filepath}:\n{df.head()}")

        if 'KEY' not in df.columns or 'VALUE' not in df.columns:
            logging.error(f"Required columns 'KEY' and 'VALUE' not found in {filepath}")
            return {}

        category_dict = dict(zip(df['KEY'], df['VALUE']))
        logging.debug(f"Loaded category mappings: {category_dict}")
        logging.info(f"Category CSV loaded successfully: {filepath}")
        return category_dict
    except Exception as e:
        logging.error(f"Error loading category CSV file {filepath}: {e}", exc_info=True)
        return {}

def get_categories_for_photobank(item, photobank_categories, category_key):
    """Get mapped categories for a specific photobank."""
    try:
        logging.debug(f"Processing categories for item with category key: {category_key}")
        logging.debug(f"Available photobank categories mapping: {photobank_categories}")
        logging.debug(f"Processing{item}")
        
        # If photobank has no category mappings, return empty list without warning
        if not photobank_categories:
            logging.debug("No category mappings available for this photobank, returning empty list")
            return []

        # Handle both formats: "photobank kategorie" and just "kategorie"
        raw_categories = item.get(category_key, '')
        logging.debug(f"RAW categories: {raw_categories}")
        
        if not raw_categories and 'kategorie' in item:
            raw_categories = item.get('kategorie', '')
            logging.debug(f"Using fallback 'kategorie' field, value: {raw_categories}")

        logging.debug(f"Raw categories from item: {raw_categories}")

        # Only log warning if photobank has category mappings but no raw categories found
        if not raw_categories and photobank_categories:
            logging.debug(f"No raw categories found for key: {category_key} and photobank has category mappings")
            return []

        # Split categories and clean them
        categories = [cat.strip() for cat in raw_categories.split(',') if cat.strip()]
        if not categories:
            logging.warning(f"No valid categories after splitting and stripping: {raw_categories}")
            return []

        # Map categories using the photobank-specific mappings
        mapped_categories = []
        for category in categories:
            mapped_value = photobank_categories.get(category)
            logging.debug(f"EVALUATING {item["Soubor"]} category {category} , mapped value {mapped_value}")
            if mapped_value:
                mapped_categories.append(mapped_value)
                logging.debug(f"Mapped category '{category}' to '{mapped_value}'")

            else:
                logging.debug(f"No mapping found for category: {category}")

        # Remove duplicates while preserving order
        mapped_categories = [str(x) for x in list(dict.fromkeys(mapped_categories))]

        logging.debug(f"Final mapped categories: {mapped_categories}")
        return mapped_categories

    except Exception as e:
        logging.error(f"Error processing categories: {e}", exc_info=True)
        return []

def load_all_categories(category_dir=CATEGORY_CSV_DIR):
    """Load all category CSV files from the specified directory and return a dictionary of mappings."""
    category_files = {photobank: f"{category_dir}/{photobank}_categories.csv" for photobank in PHOTOBANKS}
    logging.debug(f"Category files to be loaded: {category_files}")

    all_categories = {}
    for photobank, filepath in category_files.items():
        try:
            logging.debug(f"Loading categories for {photobank} from {filepath}")
            if os.path.exists(filepath):
                all_categories[photobank] = load_category_csv(filepath)
                logging.info(f"Loaded {len(all_categories[photobank])} categories for {photobank}")
            else:
                logging.debug(f"Category CSV file not found for {photobank}: {filepath}")
                all_categories[photobank] = {}
        except Exception as e:
            logging.error(f"Error loading categories for {photobank}: {e}", exc_info=True)
            all_categories[photobank] = {}

    logging.debug(f"Loaded category mappings for all photobanks: {all_categories}")
    return all_categories
