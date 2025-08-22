"""
Media processor module for running preparemediafile.py and handling media records.
"""

import csv
import json
import logging
import subprocess
import sys
from datetime import datetime
from typing import Any

from givephotobankreadymediafileslib.constants import COL_STATUS_PREFIX


def run_preparemediafile(
    file_path: str, record: dict[str, str], categories_csv: str, training_data_dir: str
) -> dict[str, Any]:
    """
    Run the preparemediafile.py script for a single file.

    Args:
        file_path: Path to the media file
        record: Record dictionary
        categories_csv: Path to the categories CSV file
        training_data_dir: Directory for storing training data

    Returns:
        Dictionary with metadata from the script output
    """
    # Convert record to JSON
    record_json = json.dumps(record, ensure_ascii=False)

    # Build command
    cmd = [
        sys.executable,
        "preparemediafile.py",
        "--file",
        file_path,
        "--record",
        record_json,
        "--categories_file",
        categories_csv,
        "--training_data_dir",
        training_data_dir,
    ]

    # Run the command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse the output JSON
        if result.stdout:
            return json.loads(result.stdout)

    except subprocess.CalledProcessError as e:
        logging.error(f"Error running preparemediafile.py: {e}")
        logging.error(f"stderr: {e.stderr}")
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing preparemediafile.py output: {e}")

    return {}


def update_record(records: list[dict[str, str]], record_index: int, metadata: dict[str, Any]) -> list[dict[str, str]]:
    """
    Update a record with new metadata.

    Args:
        records: List of all records
        record_index: Index of the record to update
        metadata: New metadata

    Returns:
        Updated list of records
    """
    if record_index < 0 or record_index >= len(records):
        logging.error(f"Invalid record index: {record_index}")
        return records

    # Update the record
    if "title" in metadata:
        records[record_index]["Název"] = metadata["title"]

    if "description" in metadata:
        records[record_index]["Popis"] = metadata["description"]

    if "keywords" in metadata:
        records[record_index]["Klíčová slova"] = ", ".join(metadata["keywords"])

    # Update categories
    if "categories" in metadata:
        # Combine all categories into a single string
        all_categories = []
        for bank, categories in metadata["categories"].items():
            if isinstance(categories, str):
                all_categories.append(categories)
            elif isinstance(categories, list):
                all_categories.extend(categories)

        # Remove duplicates and join
        unique_categories = list(dict.fromkeys(all_categories))
        records[record_index]["Kategorie"] = ", ".join(unique_categories)

    # Update status for all photobanks
    for key in records[record_index]:
        if key.startswith(COL_STATUS_PREFIX):
            records[record_index][key] = "zpracováno"

    # Update preparation date
    records[record_index]["Datum přípravy"] = datetime.now().strftime("%Y-%m-%d")

    return records


def save_records(records: list[dict[str, str]], media_csv: str) -> bool:
    """
    Save records to the CSV file.

    Args:
        records: List of records
        media_csv: Path to the media CSV file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the fieldnames from the first record
        if not records:
            logging.warning("No records to save")
            return False

        fieldnames = list(records[0].keys())

        # Write to CSV
        with open(media_csv, "w", encoding="utf-8-sig", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=",", quotechar='"')
            writer.writeheader()
            for record in records:
                writer.writerow(record)

        logging.info(f"Saved {len(records)} records to {media_csv}")
        return True

    except Exception as e:
        logging.error(f"Error saving records: {e}")
        return False
