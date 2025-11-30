import os
import re
import shutil
import logging
import csv
from typing import List, Dict
from collections import defaultdict
from tqdm import tqdm

from shared.hash_utils      import compute_file_hash
from shared.csv_sanitizer   import CSVSanitizer

def list_files(folder: str, pattern: str | None = None, recursive: bool = True) -> list[str]:
    """
    Vrátí seznam souborů ve složce `folder`.
    Pokud je zadán `pattern` (regex), vrátí jen soubory, jejichž jméno odpovídá výrazu.
    Rekurzivní prohledávání lze ovládat parametrem `recursive`.
    """
    logging.debug("Listing files in folder: %s (pattern=%s, recursive=%s)", folder, pattern, recursive)
    matched: list[str] = []
    if recursive:
        iterator = os.walk(folder)
    else:
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            iterator = [(folder, [], files)]
        except FileNotFoundError:
            logging.error("Folder not found: %s", folder)
            return []
    for root, _, files in iterator:
        for name in files:
            # pokud není zadán pattern, nebo odpovídá regexu, přidej
            if pattern is None or pattern == "" or re.search(pattern, name):
                matched.append(os.path.join(root, name))
    return matched

def copy_file(src: str, dest: str, overwrite: bool = True) -> None:
    """
    Zkopíruje soubor src do dest. Přepíše, pokud overwrite=True.
    Používá shutil.copy2 pro zachování metadat a ensure_directory pro vytvoření chybějící cesty.
    """
    logging.debug("Copying file from %s to %s (overwrite=%s)", src, dest, overwrite)
    if not overwrite and os.path.exists(dest):
        logging.debug("File exists and overwrite disabled, skipping: %s", dest)
        return

    # Vytvoří cílovou složku, pokud neexistuje
    dest_folder = os.path.dirname(dest)
    if dest_folder:
        ensure_directory(dest_folder)

    try:
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

def load_csv(path: str, encoding: str = 'utf-8-sig', delimiter: str = ',', quotechar: str = '"') -> List[Dict[str, str]]:
    """
    Load a CSV file and return a list of records as dictionaries.

    Args:
        path: Path to the CSV file
        encoding: File encoding (default: 'utf-8-sig' - UTF-8 with BOM)
        delimiter: CSV delimiter character (default: ',')
        quotechar: CSV quote character (default: '"')

    Returns:
        List of dictionaries representing CSV records

    Shows a progress bar during loading.
    """
    logging.debug("Loading CSV file from %s (encoding=%s, delimiter=%s, quotechar=%s)", path, encoding, delimiter, quotechar)
    records: List[Dict[str, str]] = []
    try:
        # Count total data rows (excluding header)
        with open(path, 'r', encoding=encoding, newline='') as csvfile:
            total_rows = sum(1 for _ in csvfile) - 1
        # Read and load records with progress bar
        with open(path, 'r', encoding=encoding, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter, quotechar=quotechar)
            for row in tqdm(reader, total=total_rows, desc="Loading CSV", unit="rows"):
                records.append(row)
        logging.info("Loaded %d records from CSV %s", len(records), path)
    except Exception as e:
        logging.error("Failed to load CSV file %s: %s", path, e)
        raise
    return records

def save_csv(records: List[Dict[str, str]], path: str) -> None:
    """
    Uloží seznam záznamů jako CSV (UTF-8 s BOM).
    Zachová hlavičku a pořadí sloupců.
    Všechny hodnoty jsou uloženy v uvozovkách, nejen ty obsahující delimiter.
    """
    logging.debug("Saving CSV file to %s", path)
    try:
        if not records:
            logging.warning("No records to save to CSV file %s", path)
            return

        # Get fieldnames from the first record
        fieldnames = list(records[0].keys())

        # Sanitize data to prevent CSV injection
        sanitized_data = CSVSanitizer.sanitize_records(records)

        with open(path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                delimiter=',',
                quotechar='"',
                quoting=csv.QUOTE_ALL  # Force quoting for all fields
            )
            writer.writeheader()
            for row in tqdm(sanitized_data, desc="Saving CSV", unit="rows"):
                writer.writerow(row)

        logging.info("Saved %d records to CSV %s", len(records), path)
    except Exception as e:
        logging.error("Failed to save CSV file %s: %s", path, e)
        raise