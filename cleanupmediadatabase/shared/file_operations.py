import csv
import json
import logging
import os
from typing import Dict, List


def ensure_directory(path: str) -> None:
    """
    Ensure that a directory exists at the given path.
    """
    logging.debug("Ensuring directory exists: %s", path)
    try:
        os.makedirs(path, exist_ok=True)
        logging.debug("Directory ready: %s", path)
    except Exception as exc:
        logging.error("Failed to ensure directory %s: %s", path, exc)
        raise


def list_files(folder: str, recursive: bool = True) -> list[str]:
    """
    List files in a folder.
    """
    files: list[str] = []
    if recursive:
        for root, _, filenames in os.walk(folder):
            for name in filenames:
                files.append(os.path.join(root, name))
    else:
        for name in os.listdir(folder):
            full_path = os.path.join(folder, name)
            if os.path.isfile(full_path):
                files.append(full_path)
    return files


def load_csv(path: str) -> List[Dict[str, str]]:
    """
    Load a CSV file into a list of records.
    """
    records: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",", quotechar="\"")
        for row in reader:
            records.append(row)
    return records


def save_csv(records: List[Dict[str, str]], path: str, fieldnames: List[str]) -> None:
    """
    Save records to a CSV file.
    """
    ensure_directory(os.path.dirname(path))
    with open(path, "w", encoding="utf-8-sig", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=",", quotechar="\"")
        writer.writeheader()
        for row in records:
            writer.writerow(row)


def save_csv_with_backup(records: List[Dict[str, str]], path: str) -> None:
    """
    Save records to a CSV file with a backup of the original.
    """
    backup_path = f"{path}.backup"
    if os.path.exists(path):
        os.replace(path, backup_path)
    fieldnames = list(records[0].keys()) if records else []
    save_csv(records, path, fieldnames)


def save_json(data: object, path: str) -> None:
    """
    Save data to a JSON file.
    """
    ensure_directory(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2, ensure_ascii=True)
