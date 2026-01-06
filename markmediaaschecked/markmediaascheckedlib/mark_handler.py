"""
Handler module for marking media as checked in CSV files.
"""
import os
import logging
from typing import List, Dict
from markmediaascheckedlib.constants import (
    STATUS_COLUMN_KEYWORD,
    STATUS_READY,
    STATUS_CHECKED,
    COL_FILE,
    COL_PATH,
    ALTERNATIVE_EDIT_TAGS
)


def extract_status_columns(records: list[dict]) -> list[str]:
    """
    Vrátí seznam názvů sloupců, které obsahují podřetězec STATUS_COLUMN_KEYWORD.
    Hledání je case-insensitive.
    """
    if not records or len(records) == 0:
        logging.warning("No records provided to extract status columns from")
        return []

    # Get the first record to extract column names
    first_record = records[0]

    # Find all columns containing 'status' (case-insensitive)
    status_columns = [col for col in first_record.keys()
                     if STATUS_COLUMN_KEYWORD.lower() in col.lower()]

    logging.info(f"Found {len(status_columns)} status columns: {', '.join(status_columns)}")
    return status_columns


def filter_ready_records(records: list[dict], status_columns: list[str]) -> list[dict]:
    """
    Vrátí seznam záznamů, kde alespoň jeden statusový sloupec obsahuje hodnotu STATUS_READY.
    """
    if not records:
        logging.warning("No records provided to filter")
        return []

    if not status_columns:
        logging.warning("No status columns provided for filtering")
        return []

    ready_records = []
    for record in records:
        for col in status_columns:
            if col in record and record[col] == STATUS_READY:
                ready_records.append(record)
                break  # Once we find one STATUS_READY, we can add the record and move on

    logging.info(f"Found {len(ready_records)} records with status '{STATUS_READY}'")
    return ready_records


def update_statuses(records: list[dict], status_columns: list[str]) -> int:
    """
    V každém statusovém sloupci v každém záznamu nahradí STATUS_READY → STATUS_CHECKED.
    Vrací počet provedených změn.
    """
    if not records:
        logging.warning("No records provided to update")
        return 0

    if not status_columns:
        logging.warning("No status columns provided for updating")
        return 0

    change_count = 0
    for record in records:
        for col in status_columns:
            if col in record and record[col] == STATUS_READY:
                record[col] = STATUS_CHECKED
                change_count += 1

    logging.info(f"Updated {change_count} status values from '{STATUS_READY}' to '{STATUS_CHECKED}'")
    return change_count


def update_statuses_with_report(records: list[dict], status_columns: list[str]) -> list[dict]:
    """
    Update statuses and return detailed change records for reporting.
    """
    if not records:
        logging.warning("No records provided to update")
        return []

    if not status_columns:
        logging.warning("No status columns provided for updating")
        return []

    changes: list[dict] = []
    for record in records:
        file_name = record.get(COL_FILE, "")
        for col in status_columns:
            if col in record and record[col] == STATUS_READY:
                record[col] = STATUS_CHECKED
                changes.append({
                    "file": file_name,
                    "status_column": col,
                    "old_status": STATUS_READY,
                    "new_status": STATUS_CHECKED
                })

    logging.info("Updated %d status values with report", len(changes))
    return changes


def is_edited_photo(record: dict) -> bool:
    """
    Check if record is an edited photo based on filename edit tags.

    Args:
        record: CSV record dictionary

    Returns:
        True if filename contains any edit tag (_bw, _negative, _sharpen, _misty, _blurred), False otherwise
    """
    filename = record.get(COL_FILE, '')
    if not filename:
        return False

    # Check if filename contains any edit tag
    filename_lower = filename.lower()
    name_without_ext = os.path.splitext(filename_lower)[0]

    for tag in ALTERNATIVE_EDIT_TAGS.keys():
        if name_without_ext.endswith(tag):
            return True

    return False


def filter_records_by_edit_type(records: list[dict], include_edited: bool = False) -> list[dict]:
    """
    Filter records based on whether they are edited photos.

    Logic:
    - Edited photos (with edit tags like _bw, _negative): included only if include_edited=True
    - Original photos (without edit tags): always included

    Note: Alternative FORMATS (PNG, TIF) are not in MediaCSV at all, so no filtering needed.

    Args:
        records: List of CSV records
        include_edited: If True, include edited photos with edit tags

    Returns:
        Filtered list of records
    """
    if not records:
        return []

    filtered = []
    excluded_edited = 0

    for record in records:
        # Exclude edited photos if include_edited=False
        if not include_edited and is_edited_photo(record):
            excluded_edited += 1
            filename = record.get(COL_FILE, 'unknown')
            logging.debug(f"Excluding edited photo: {filename}")
            continue

        filtered.append(record)

    logging.info(f"Filtered {len(filtered)} records from {len(records)} total "
                f"(excluded {excluded_edited} edited photos)")

    return filtered
