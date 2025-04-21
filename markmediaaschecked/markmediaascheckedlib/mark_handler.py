"""
Handler module for marking media as checked in CSV files.
"""
import logging
from typing import List, Dict
from markmediaascheckedlib.constants import STATUS_COLUMN_KEYWORD, STATUS_READY, STATUS_CHECKED


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
