import os
import csv
import logging
import shutil
from datetime import datetime
from typing import List, Dict
from tqdm import tqdm

from shared.csv_sanitizer import CSVSanitizer

def load_csv(path: str) -> List[Dict[str, str]]:
    """
    Load a CSV file and return a list of records as dictionaries.
    Assumes comma delimiter and UTF-8 with BOM (utf-8-sig).
    Shows a progress bar during loading.
    """
    logging.debug(f"Loading CSV file from {path}")
    records: List[Dict[str, str]] = []
    
    try:
        if not os.path.exists(path):
            logging.warning(f"CSV file does not exist: {path}")
            return []
            
        # Count total data rows (excluding header)
        with open(path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            total_rows = sum(1 for _ in csvfile) - 1
            
        # Read and load records with progress bar
        with open(path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in tqdm(reader, total=total_rows, desc="Loading CSV", unit="rows"):
                records.append(row)
                
        logging.info(f"Loaded {len(records)} records from CSV {path}")
    except Exception as e:
        logging.error(f"Failed to load CSV file {path}: {e}")
        raise
        
    return records

def save_csv(path: str, records: List[Dict[str, str]], backup: bool = True) -> None:
    """
    Save records to a CSV file.
    If backup=True, creates a backup of the existing file with timestamp.
    Assumes comma delimiter and UTF-8 with BOM (utf-8-sig).
    Shows a progress bar during saving.
    """
    logging.debug(f"Saving CSV file to {path}")
    
    try:
        # Create backup if requested and file exists
        if backup and os.path.exists(path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{path}.{timestamp}.bak"
            shutil.copy2(path, backup_path)
            logging.info(f"Created backup of CSV file: {backup_path}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Get fieldnames from all records (union of all keys)
        fieldnames = set()
        for record in records:
            fieldnames.update(record.keys())
        fieldnames = sorted(list(fieldnames))
        
        # Sanitize data to prevent CSV injection
        sanitized_data = sanitize_records(records)

        # Write records to CSV with progress bar
        with open(path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()

            for record in tqdm(sanitized_data, desc="Saving CSV", unit="rows"):
                writer.writerow(record)
                
        logging.info(f"Saved {len(records)} records to CSV {path}")
    except Exception as e:
        logging.error(f"Failed to save CSV file {path}: {e}")
        raise
