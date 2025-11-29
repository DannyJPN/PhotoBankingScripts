
import logging
import csv
from typing import List, Dict
from tqdm import tqdm
import os
import shutil

def copy_file(src: str, dest: str, overwrite: bool = True) -> None:
    """
    Copy a file from src to dest using shutil.copy2 for proper metadata preservation.
    
    Args:
        src: Source file path
        dest: Destination file path
        overwrite: Whether to overwrite existing files
    """
    logging.debug("Copying file from %s to %s (overwrite=%s)", src, dest, overwrite)
    if not overwrite and os.path.exists(dest):
        logging.debug("File exists and overwrite disabled, skipping: %s", dest)
        return
    
    try:
        # Ensure destination directory exists
        dest_dir = os.path.dirname(dest)
        if dest_dir:
            ensure_directory(dest_dir)
        
        # Copy file with metadata preservation
        shutil.copy2(src, dest)
        logging.debug("Copied file from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to copy file from %s to %s: %s", src, dest, e)
        raise

def ensure_directory(path: str) -> None:
    """
    Ensure that a directory exists at the given path.
    Creates the directory if it does not exist.
    """
    logging.debug("Ensuring directory exists: %s", path)
    try:
        os.makedirs(path, exist_ok=True)
        logging.debug("Directory ready: %s", path)
    except Exception as e:
        logging.error("Failed to ensure directory %s: %s", path, e)
        raise


def load_csv(path: str) -> List[Dict[str, str]]:
    """
    Load a CSV file and return a list of records as dictionaries.
    Assumes comma delimiter and UTF-8 with BOM (utf-8-sig).
    Shows a progress bar during loading.
    """
    logging.debug("Loading CSV file from %s", path)
    records: List[Dict[str, str]] = []
    try:
        # Count total data rows (excluding header)
        with open(path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            total_rows = sum(1 for _ in csvfile) - 1
        # Read and load records with progress bar
        with open(path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in tqdm(reader, total=total_rows, desc="Loading CSV", unit="rows"):
                records.append(row)
        logging.info("Loaded %d records from CSV %s", len(records), path)
    except Exception as e:
        logging.error("Failed to load CSV file %s: %s", path, e)
        raise
    return records


def save_csv(records: List[Dict[str, str]], path: str, sanitize: bool = True) -> None:
    """
    Save a list of records as CSV (UTF-8 with BOM).
    Preserves header and column order.
    All values are quoted, not just those containing delimiters.

    Args:
        records: List of dictionaries to save
        path: Output file path
        sanitize: Whether to sanitize data to prevent CSV injection (default: True)
    """
    logging.debug("Saving CSV file to %s (sanitize=%s)", path, sanitize)
    try:
        if not records:
            logging.warning("No records to save to CSV file %s", path)
            return

        # Sanitize records to prevent CSV injection attacks
        if sanitize:
            from shared.csv_sanitizer import CSVSanitizer
            records = CSVSanitizer.sanitize_records(records)
            logging.debug("Applied CSV injection protection to %d records", len(records))

        # Get fieldnames from the first record
        fieldnames = list(records[0].keys())

        with open(path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                delimiter=',',
                quotechar='"',
                quoting=csv.QUOTE_ALL  # Force quoting for all fields
            )
            writer.writeheader()
            for row in tqdm(records, desc="Saving CSV", unit="rows"):
                writer.writerow(row)

        logging.info("Saved %d sanitized records to CSV %s", len(records), path)
    except Exception as e:
        logging.error("Failed to save CSV file %s: %s", path, e)
        raise