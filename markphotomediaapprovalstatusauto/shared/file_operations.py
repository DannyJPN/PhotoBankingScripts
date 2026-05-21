"""Centralised file and data I/O helpers for all photobank scripts."""

import os
import re
import shutil
import logging
import csv
import json
from typing import Any, Dict, List
from collections import defaultdict
from tqdm import tqdm

from shared.hash_utils import compute_file_hash
from shared.csv_sanitizer import sanitize_field, sanitize_record, sanitize_records, is_dangerous

def list_files(folder: str, pattern: str | None = None, recursive: bool = True) -> list[str]:
    """Return a list of file paths inside *folder*.

    :param folder: Root directory to search.
    :param pattern: Optional regex applied to each filename (basename only). When ``None``
        or empty, all files are included.
    :param recursive: When ``True`` (default) the search descends into sub-directories.
    :return: List of absolute file paths matching the given criteria.
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
            if pattern is None or pattern == "" or re.search(pattern, name):
                matched.append(os.path.join(root, name))
    return matched

def copy_folder(src: str, dest: str, overwrite: bool = True, pattern: str = "") -> None:
    """
    Copies files from src to dest folder (recursively).
    Only copies files matching the regex `pattern`. If pattern is empty, all files are copied.
    Shows a progress bar for each file.
    """
    logging.debug("Copying folder from %s to %s (overwrite=%s, pattern=%s)", src, dest, overwrite, pattern)
    try:
        if os.path.exists(dest) and not overwrite:
            logging.debug("Destination folder exists and overwrite is disabled, skipping copy.")
            return

        files = list_files(src, recursive=True)
        if pattern:
            regex = re.compile(pattern, re.IGNORECASE)
            files = [f for f in files if regex.search(os.path.basename(f))]

        if not files:
            logging.info("No files to copy from %s to %s", src, dest)
            return

        for file_path in tqdm(files, desc="Copying folder", unit="file"):
            rel_path = os.path.relpath(file_path, src)
            dest_path = os.path.join(dest, rel_path)
            copy_file(file_path, dest_path, overwrite=overwrite)

        logging.info("Copied folder from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to copy folder from %s to %s: %s", src, dest, e)
        raise

def delete_folder(path: str) -> None:
    """Delete an entire directory tree.

    :param path: Path to the directory to remove.
    :raises Exception: Re-raises any OS-level error after logging it.
    """
    logging.debug("Deleting folder: %s", path)
    try:
        shutil.rmtree(path)
        logging.info("Deleted folder: %s", path)
    except Exception as e:
        logging.error("Failed to delete folder %s: %s", path, e)
        raise

def move_folder(src: str, dest: str, overwrite: bool = False, pattern: str = "") -> None:
    """
    Moves files from src to dest folder (recursively).
    Only moves files matching the regex `pattern`. If pattern is empty, all files are moved.
    Shows a progress bar for each file.
    """
    logging.debug("Moving folder from %s to %s (overwrite=%s, pattern=%s)", src, dest, overwrite, pattern)
    try:
        if os.path.exists(dest):
            if overwrite:
                shutil.rmtree(dest)
                logging.debug("Existing destination folder deleted: %s", dest)
            else:
                logging.debug("Destination folder exists and overwrite is disabled, skipping move.")
                return

        files = list_files(src, recursive=True)
        if pattern:
            regex = re.compile(pattern, re.IGNORECASE)
            files = [f for f in files if regex.search(os.path.basename(f))]

        if not files:
            logging.info("No files to move from %s to %s", src, dest)
            return

        for file_path in tqdm(files, desc="Moving folder", unit="file"):
            rel_path = os.path.relpath(file_path, src)
            dest_path = os.path.join(dest, rel_path)
            move_file(file_path, dest_path, overwrite=overwrite)

        delete_folder(src)
        logging.info("Moved folder from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to move folder from %s to %s: %s", src, dest, e)
        raise
def copy_file(src: str, dest: str, overwrite: bool = True) -> None:
    """Copy *src* to *dest*, preserving file metadata.

    :param src: Source file path.
    :param dest: Destination file path.
    :param overwrite: When ``False`` and *dest* already exists the copy is skipped. Defaults to ``True``.
    :raises Exception: Re-raises any OS-level error after logging it.
    """
    logging.debug("Copying file from %s to %s (overwrite=%s)", src, dest, overwrite)
    if not overwrite and os.path.exists(dest):
        logging.debug("File exists and overwrite disabled, skipping: %s", dest)
        return

    # Ensure destination directory exists
    dest_folder = os.path.dirname(dest)
    if dest_folder:
        ensure_directory(dest_folder)

    try:
        shutil.copy2(src, dest)
        logging.debug("Copied file from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to copy file from %s to %s: %s", src, dest, e)
        raise

def move_file(src: str, dest: str, overwrite: bool = False) -> None:
    """Move *src* to *dest*, creating the destination directory if needed.

    :param src: Source file path.
    :param dest: Destination file path.
    :param overwrite: When ``False`` (default) and *dest* already exists the move is skipped.
    :raises Exception: Re-raises any OS-level error after logging it.
    """
    logging.debug("Moving file from %s to %s (overwrite=%s)", src, dest, overwrite)

    # Ensure destination directory exists
    dest_folder = os.path.dirname(dest)
    if dest_folder:
        ensure_directory(dest_folder)

    if not overwrite and os.path.exists(dest):
        logging.debug("File exists and overwrite disabled, skipping move: %s", dest)
        return

    try:
        shutil.move(src, dest)
        logging.debug("Moved file from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to move file from %s to %s: %s", src, dest, e)
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

def unify_duplicate_files(folder: str, recursive: bool = True) -> None:
    """Rename duplicate files in *folder* so they all share the shortest basename.

    Files with identical content (same SHA-256 hash) are considered duplicates.
    Among each group the file whose basename is shortest is chosen as canonical;
    all other copies are renamed to that basename.

    :param folder: Directory to scan for duplicates.
    :param recursive: When ``True`` (default) sub-directories are also scanned.
    """
    logging.info("Unifying duplicates in %s (recursive=%s)", folder, recursive)

    path_hash_map = get_hash_map_from_folder(folder, pattern="", recursive=recursive)
    if not path_hash_map:
        logging.info("No files found in %s, skipping unification.", folder)
        return

    hash_groups: dict[str, list[str]] = defaultdict(list)
    for path, h in path_hash_map.items():
        hash_groups[h].append(path)

    # Check if there are any duplicate groups
    duplicate_groups = [(h, group) for h, group in hash_groups.items() if len(group) >= 2]
    if not duplicate_groups:
        logging.info("No duplicate files found in %s", folder)
        return

    renamed_count = 0
    for h, group in hash_groups.items():
        if len(group) < 2:
            continue

        canonical_path = min(group, key=lambda p: len(os.path.basename(p)))
        canonical_basename = os.path.basename(canonical_path)
        logging.debug("Hash %s has %d duplicates, canonical = %s", h, len(group), canonical_basename)

        for path in group:
            current_name = os.path.basename(path)
            if current_name == canonical_basename:
                continue

            dst = os.path.join(os.path.dirname(path), canonical_basename)
            try:
                os.replace(path, dst)
                renamed_count += 1
                logging.info("Renamed %s -> %s", path, dst)
            except Exception as e:
                logging.error("Failed to rename %s to %s: %s", path, dst, e)

    logging.info("Unification complete: renamed %d duplicate files in %s", renamed_count, folder)

def get_hash_map_from_folder(folder: str, pattern: str = "PICT", recursive: bool = True) -> Dict[str, str]:
    """Build a mapping of file paths to their SHA-256 hashes.

    :param folder: Directory to scan.
    :param pattern: Regex filter applied to filenames. Defaults to ``"PICT"``.
    :param recursive: When ``True`` (default) sub-directories are included.
    :return: Dict mapping absolute file path → hash string.
    """
    logging.info("Building hash map from folder: %s (pattern=%s)", folder, pattern)
    paths = list_files(folder, pattern, recursive=recursive)
    if not paths:
        logging.info("No files matching pattern '%s' in %s, skipping.", pattern, folder)
        return {}
    result: Dict[str, str] = {}
    for path in tqdm(paths, desc="Hashing files", unit="files"):
        try:
            file_hash = compute_file_hash(path)
            result[path] = file_hash
        except Exception as e:
            logging.error("Failed to hash %s: %s", path, e)
    logging.info("Built hash map with %d entries from %s", len(result), folder)
    return result


def save_csv_with_backup(data: List[Dict[str, str]], path: str) -> None:
    """Write *data* to a CSV file, first creating a timestamped backup of the original.

    :param data: List of dicts representing CSV rows; keys become column headers.
    :param path: Destination CSV file path.
    :raises Exception: Re-raises any write error after logging it.
    """
    from datetime import datetime

    logging.info("Saving CSV with backup: %s", path)

    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{os.path.splitext(path)[0]}_{timestamp}.csv"

    # Create backup
    copy_file(path, backup_path)
    logging.info("Created backup at: %s", backup_path)

    # Ensure the directory exists
    ensure_directory(os.path.dirname(path))

    # Write the updated CSV
    try:
        # Get fieldnames from the first row
        fieldnames = list(data[0].keys()) if data else []

        # Sanitize data to prevent CSV injection
        sanitized_data = sanitize_records(data)

        with open(path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
            writer.writeheader()
            writer.writerows(sanitized_data)

        logging.info("Successfully saved %d records to %s", len(data), path)
    except Exception as e:
        logging.error("Failed to save CSV file %s: %s", path, e)
        raise


def load_json_file(path: str) -> Any:
    """Load and parse a JSON file.

    :param path: Path to the JSON file.
    :return: Parsed JSON value (dict, list, or scalar).
    """
    logging.debug("Loading JSON file from %s", path)
    with open(path, "r", encoding="utf-8") as jsonfile:
        return json.load(jsonfile)


def save_json_file(path: str, data: Any, ensure_ascii: bool = True, indent: int = 2) -> None:
    """Serialise *data* to a JSON file, creating any missing parent directories.

    :param path: Destination file path.
    :param data: JSON-serialisable value to write.
    :param ensure_ascii: When ``True`` (default) non-ASCII characters are escaped.
    :param indent: Pretty-print indentation level.
    """
    logging.debug("Saving JSON file to %s", path)
    folder = os.path.dirname(path)
    if folder:
        ensure_directory(folder)
    with open(path, "w", encoding="utf-8") as jsonfile:
        json.dump(data, jsonfile, indent=indent, ensure_ascii=ensure_ascii)
