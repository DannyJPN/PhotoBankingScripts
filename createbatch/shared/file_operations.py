import csv
import logging
import os

from tqdm import tqdm


def copy_file(src: str, dest: str, overwrite: bool = True) -> None:
    """
    Copy a file from src to dest. Overwrite if specified.
    """
    logging.debug("Copying file from %s to %s (overwrite=%s)", src, dest, overwrite)
    if not overwrite and os.path.exists(dest):
        logging.debug("File exists and overwrite disabled, skipping: %s", dest)
        return
    try:
        with open(src, "rb") as fsrc, open(dest, "wb") as fdest:
            fdest.write(fsrc.read())
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


def load_csv(path: str) -> list[dict[str, str]]:
    """
    Load a CSV file and return a list of records as dictionaries.
    Assumes comma delimiter and UTF-8 with BOM (utf-8-sig).
    Shows a progress bar during loading.
    """
    logging.debug("Loading CSV file from %s", path)
    records: list[dict[str, str]] = []
    try:
        # Count total data rows (excluding header)
        with open(path, encoding="utf-8-sig", newline="") as csvfile:
            total_rows = sum(1 for _ in csvfile) - 1
        # Read and load records with progress bar
        with open(path, encoding="utf-8-sig", newline="") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
            for row in tqdm(reader, total=total_rows, desc="Loading CSV", unit="rows"):
                records.append(row)
        logging.info("Loaded %d records from CSV %s", len(records), path)
    except Exception as e:
        logging.error("Failed to load CSV file %s: %s", path, e)
        raise
    return records
