"""
Media info loader for loading media records and categories from CSV files.
"""

import os
import logging
from typing import List, Dict

from shared.file_operations import load_csv
from givephotobankreadymediafileslib.constants import (
    COL_FILE, COL_PATH, COL_ORIGINAL, COL_CREATE_DATE
)


def load_media_records(csv_path: str) -> List[Dict[str, str]]:
    """
    Load all media records from PhotoMedia.csv.
    
    Args:
        csv_path: Path to PhotoMedia.csv file
        
    Returns:
        List of all media record dictionaries
    """
    logging.info(f"Loading media records from {csv_path}")
    
    if not os.path.exists(csv_path):
        logging.error(f"Media CSV file not found: {csv_path}")
        return []
    
    # Use file_operations to load CSV
    records = load_csv(csv_path)
    logging.info(f"Loaded {len(records)} media records")
    
    return records


def load_categories(csv_path: str) -> Dict[str, List[str]]:
    """
    Load photobank categories from PhotoCategories.csv.
    
    Args:
        csv_path: Path to PhotoCategories.csv file
        
    Returns:
        Dictionary mapping photobank names to lists of categories
    """
    logging.info(f"Loading categories from {csv_path}")
    
    if not os.path.exists(csv_path):
        logging.warning(f"Categories CSV file not found: {csv_path}")
        return {}
    
    try:
        # Use file_operations to load CSV
        records = load_csv(csv_path)
        
        if not records:
            logging.warning("No category records found")
            return {}
        
        # Convert to photobank->categories mapping
        categories = {}
        
        # First record should contain photobank names as keys
        first_record = records[0]
        for photobank in first_record.keys():
            if photobank:  # Skip empty keys
                categories[photobank] = []
        
        # Collect all categories for each photobank
        for record in records:
            for photobank, category in record.items():
                if photobank in categories and category:
                    categories[photobank].append(category)
        
        logging.info(f"Loaded categories for {len(categories)} photobanks")
        for bank, cats in categories.items():
            logging.debug(f"{bank}: {len(cats)} categories")
        
        return categories
        
    except Exception as e:
        logging.error(f"Error loading categories: {e}")
        return {}

