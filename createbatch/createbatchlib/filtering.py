import logging
import re
from typing import List, Dict
from createbatchlib.constants import STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE, EDITORIAL_REGEX, BANKS_NO_EDITORIAL

def filter_prepared_media(records: List[Dict[str, str]], include_edited: bool = False) -> List[Dict[str, str]]:
    """
    Filter records to include only those marked as PREPARED_STATUS_VALUE in any status field.

    This function operates without a progress bar as it's typically a fast operation.
    Progress information is logged instead.

    Args:
        records: List of media records from CSV
        include_edited: If False (default), exclude edited photos from 'upravené' folders.
                       If True, include all photos (original and edited).

    Returns:
        List of filtered records that match the prepared status criteria
    """
    total = len(records)
    logging.info("Loading and filtering records from %d total records (include_edited=%s)", total, include_edited)
    filtered: List[Dict[str, str]] = []
    excluded_edited_count = 0

    for record in records:
        # Check if record has PREPARED status
        # NOTE: Using exact match to avoid matching 'nepřipraveno' when looking for 'připraveno'
        has_prepared_status = False
        for key, value in record.items():
            if STATUS_FIELD_KEYWORD in key.lower() and isinstance(value, str) and value.strip().lower() == PREPARED_STATUS_VALUE.lower():
                has_prepared_status = True
                break

        if not has_prepared_status:
            continue

        # Check if it's an edited photo and should be excluded
        if not include_edited:
            file_path = record.get('Cesta', '')
            if file_path and 'upravené' in file_path.lower():
                excluded_edited_count += 1
                logging.debug("Excluding edited photo: %s", file_path)
                continue

        filtered.append(record)

    logging.info("Filtered %d prepared media records out of %d (excluded %d edited photos)",
                 len(filtered), total, excluded_edited_count)
    return filtered


def is_editorial_record(record: Dict[str, str]) -> bool:
    """
    Check if a record is editorial content based on title or description.

    Args:
        record: Record dictionary from PhotoMedia.csv

    Returns:
        True if record matches editorial regex pattern
    """
    title = record.get('Název', record.get('title', record.get('Title', '')))
    description = record.get('Popis', record.get('description', record.get('Description', '')))

    return bool(re.search(EDITORIAL_REGEX, title)) or bool(re.search(EDITORIAL_REGEX, description))


def should_skip_editorial_for_bank(record: Dict[str, str], bank_name: str) -> bool:
    """
    Determine if an editorial record should be skipped for a given bank.

    Args:
        record: Record dictionary from PhotoMedia.csv
        bank_name: Name of the photobank

    Returns:
        True if record is editorial and bank doesn't accept editorial
    """
    if bank_name not in BANKS_NO_EDITORIAL:
        return False

    return is_editorial_record(record)


def filter_editorial_for_bank(records: List[Dict[str, str]], bank_name: str) -> List[Dict[str, str]]:
    """
    Filter out editorial records for banks that don't accept editorial content.

    Args:
        records: List of records to filter
        bank_name: Name of the photobank

    Returns:
        Filtered list of records (editorial removed if bank doesn't support it)
    """
    if bank_name not in BANKS_NO_EDITORIAL:
        return records

    original_count = len(records)
    filtered = [rec for rec in records if not is_editorial_record(rec)]
    filtered_count = original_count - len(filtered)

    if filtered_count > 0:
        logging.info(f"Filtered out {filtered_count} editorial records for {bank_name} (does not accept editorial)")

    return filtered