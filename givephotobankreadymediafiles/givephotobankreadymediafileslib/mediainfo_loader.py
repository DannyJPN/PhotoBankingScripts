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


def parse_dreamstime_hierarchy(categories: List[str]) -> Dict[str, List[str]]:
    """
    Parse Dreamstime categories from flat list into hierarchical structure.

    Dreamstime categories have format "MainCategory -> SubCategory".
    This function groups them by main category for better prompt formatting.

    Args:
        categories: List of category strings like ["Abstract -> Aerial", "Animals -> Birds"]

    Returns:
        Dict mapping main category to list of sub-categories, e.g.:
        {"Abstract": ["Aerial", "Backgrounds"], "Animals": ["Birds", "Farm"]}
    """
    hierarchy: Dict[str, List[str]] = {}

    for category in categories:
        if " -> " not in category:
            continue

        parts = category.split(" -> ", 1)
        if len(parts) != 2:
            continue

        main_cat = parts[0].strip()
        sub_cat = parts[1].strip()

        if not main_cat or not sub_cat:
            continue

        if main_cat not in hierarchy:
            hierarchy[main_cat] = []

        if sub_cat not in hierarchy[main_cat]:
            hierarchy[main_cat].append(sub_cat)

    sorted_hierarchy: Dict[str, List[str]] = {}
    for main_cat in sorted(hierarchy.keys()):
        sorted_hierarchy[main_cat] = sorted(hierarchy[main_cat])

    return sorted_hierarchy


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

