"""
Status handler for the markphotomediaapprovalstatus script.
"""

import os
import logging
from typing import List, Dict, Optional
from markphotomediaapprovalstatuslib.constants import (
    STATUS_CHECKED,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_MAYBE,
    STATUS_BACKUP,
    STATUS_PREPARED,
    STATUS_UNUSED,
    INPUT_APPROVE,
    INPUT_REJECT,
    INPUT_MAYBE,
    STATUS_COLUMN_KEYWORD,
    COL_FILE,
    COL_PATH,
    COL_ORIGINAL,
    ORIGINAL_YES,
    EDIT_SHARPEN,
    ALTERNATIVE_EDIT_TAGS
)


def process_bank_status_updates(data: List[Dict[str, str]], bank: str, log_path: str) -> bool:
    """
    Process status updates for a specific bank.

    Args:
        data: List of dictionaries representing CSV rows
        bank: Name of the bank to process
        log_path: Path to the log file

    Returns:
        True if any changes were made, False otherwise
    """
    logging.info(f"Processing status updates for {bank}")

    # Column name for this bank's status
    status_column = f"{bank} status"
    changes_made = False

    # Process each entry
    for entry in data:
        # Skip if this entry doesn't have the status column or it's not set to STATUS_CHECKED
        if status_column not in entry or entry[status_column] != STATUS_CHECKED:
            continue

        # Display information about the file
        file_name = entry.get("Soubor", "Unknown")
        title = entry.get("Název", "")
        description = entry.get("Popis", "")
        keywords = entry.get("Klíčová slova", "")

        print("\n" + "=" * 50)
        print(f"File: {file_name}")
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"Keywords: {keywords}")
        print("=" * 50)

        # Ask for user input
        prompt = f"Was file {file_name} accepted on {bank}? (a = yes, n = no, m = maybe): "
        user_input = input(prompt).strip().lower()

        # Process user input
        if user_input == INPUT_APPROVE:
            entry[status_column] = STATUS_APPROVED
            changes_made = True
            log_result(log_path, file_name, bank, INPUT_APPROVE)
        elif user_input == INPUT_REJECT:
            entry[status_column] = STATUS_REJECTED
            changes_made = True
            log_result(log_path, file_name, bank, INPUT_REJECT)
        elif user_input == INPUT_MAYBE:
            entry[status_column] = STATUS_MAYBE
            changes_made = True
            log_result(log_path, file_name, bank, INPUT_MAYBE)
        else:
            print(f"File {file_name} not evaluated - invalid response.")

    logging.info(f"Completed processing for {bank}, changes made: {changes_made}")
    return changes_made


def log_result(log_path: str, file_name: str, bank: str, result: str) -> None:
    """
    Log the result of a status update.

    Args:
        log_path: Path to the log file
        file_name: Name of the file
        bank: Name of the bank
        result: Result of the status update (a/n/m)
    """
    try:
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"{file_name} : {bank} : {result}\n")
        logging.debug(f"Logged result for {file_name} on {bank}: {result}")
    except Exception as e:
        logging.error(f"Failed to log result: {e}")


def extract_status_columns(records: List[Dict[str, str]]) -> List[str]:
    """
    Returns a list of column names that contain the STATUS_COLUMN_KEYWORD substring.
    The search is case-insensitive.

    Args:
        records: List of dictionaries representing CSV rows

    Returns:
        List of column names containing the STATUS_COLUMN_KEYWORD
    """
    if not records or len(records) == 0:
        logging.warning("No records provided to extract status columns from")
        return []

    # Get the first record to extract column names
    first_record = records[0]

    # Find all columns containing STATUS_COLUMN_KEYWORD (case-insensitive)
    status_columns = [col for col in first_record.keys()
                     if STATUS_COLUMN_KEYWORD.lower() in col.lower()]

    logging.info(f"Found {len(status_columns)} status columns: {', '.join(status_columns)}")
    return status_columns


def filter_records_by_status(records: List[Dict[str, str]], status_value: str) -> List[Dict[str, str]]:
    """
    Returns a list of records where at least one status column contains the specified status value.

    Args:
        records: List of dictionaries representing CSV rows
        status_value: The status value to filter by

    Returns:
        List of dictionaries containing only entries with at least one status column set to status_value
    """
    if not records:
        logging.warning("No records provided to filter")
        return []

    logging.debug(f"Filtering entries with '{status_value}' status")

    # Get status columns
    status_columns = extract_status_columns(records)
    if not status_columns:
        logging.warning("No status columns found for filtering")
        return []

    filtered_records = []
    for record in records:
        for col in status_columns:
            if col in record and record[col] == status_value:
                filtered_records.append(record)
                break  # Once we find one matching status, we can add the record and move on

    logging.info(f"Found {len(filtered_records)} records with status '{status_value}'")
    return filtered_records


def filter_checked_entries(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Returns a list of entries that have STATUS_CHECKED value in any status column.

    Args:
        data: List of dictionaries representing CSV rows

    Returns:
        List of dictionaries containing only entries with at least one status column set to STATUS_CHECKED
    """
    return filter_records_by_status(data, STATUS_CHECKED)


def filter_records_by_bank_status(
    records: List[Dict[str, str]],
    bank: str,
    status_value: str
) -> List[Dict[str, str]]:
    """
    Filter records where a specific bank's status column has the given value.

    This enables bank-first iteration by filtering records that need processing
    for a particular photobank.

    Args:
        records: List of dictionaries representing CSV rows
        bank: Bank name (e.g., "ShutterStock", "AdobeStock")
        status_value: Status to match (e.g., "kontrolováno", "připraveno")

    Returns:
        List of records where the specified bank's status column equals status_value

    Example:
        >>> shutterstock_records = filter_records_by_bank_status(
        ...     all_records, "ShutterStock", "kontrolováno"
        ... )
        >>> # Returns only records with "ShutterStock status" = "kontrolováno"
    """
    if not records:
        logging.warning("No records provided to filter by bank status")
        return []

    status_column = f"{bank} {STATUS_COLUMN_KEYWORD}"
    logging.debug(f"Filtering records for bank '{bank}' with status '{status_value}' (column: {status_column})")

    filtered = []
    for record in records:
        if status_column in record and record[status_column] == status_value:
            filtered.append(record)

    logging.info(f"Found {len(filtered)} records for {bank} with status '{status_value}'")
    return filtered


def find_sharpen_for_original(original_filename: str, all_records: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Najde _sharpen verzi originálu v seznamu záznamů.

    Args:
        original_filename: Název originálního souboru (např. "photo.jpg")
        all_records: Všechny záznamy v CSV

    Returns:
        Záznam _sharpen verze nebo None pokud neexistuje
    """
    # Sestavit očekávaný název _sharpen souboru
    base_name, ext = os.path.splitext(original_filename)
    expected_sharpen_name = f"{base_name}{EDIT_SHARPEN}{ext}"

    # Hledat záznam s tímto názvem
    for record in all_records:
        if record.get(COL_FILE, '') == expected_sharpen_name:
            logging.debug(f"Found _sharpen version for {original_filename}: {expected_sharpen_name}")
            return record

    logging.debug(f"No _sharpen version found for {original_filename}")
    return None


def update_sharpen_status(original_record: Dict[str, str], all_records: List[Dict[str, str]],
                         bank: str, new_original_status: str) -> bool:
    """
    Aktualizuje status _sharpen souboru na základě statusu originálu.

    Logika:
    - Originál schválen (STATUS_APPROVED) → _sharpen: "záložní" → "nepoužito"
    - Originál zamítnut (STATUS_REJECTED) → _sharpen: "záložní" → "připraveno"
    - Originál "možná" (STATUS_MAYBE) → _sharpen: beze změny

    Args:
        original_record: Záznam originálního souboru
        all_records: Všechny záznamy v CSV (pro hledání _sharpen)
        bank: Název banky (pro správný status sloupec)
        new_original_status: Nový status originálu (schváleno/zamítnuto/možná)

    Returns:
        True pokud byl _sharpen status změněn, jinak False
    """
    # Zkontroluj, jestli je to skutečně originál
    if original_record.get(COL_ORIGINAL, '').strip().lower() != ORIGINAL_YES.lower():
        logging.debug(f"Record {original_record.get(COL_FILE)} is not an original, skipping _sharpen check")
        return False

    # Najdi _sharpen verzi
    original_filename = original_record.get(COL_FILE, '')
    if not original_filename:
        logging.warning("Original record has no filename, cannot find _sharpen")
        return False

    sharpen_record = find_sharpen_for_original(original_filename, all_records)
    if not sharpen_record:
        # Není chyba, ne všechny fotky mají _sharpen verzi
        logging.debug(f"No _sharpen version exists for {original_filename}, skipping")
        return False

    # Získej status column pro tuto banku
    status_column = f"{bank} {STATUS_COLUMN_KEYWORD}"
    if status_column not in sharpen_record:
        logging.warning(f"_sharpen record {sharpen_record.get(COL_FILE)} doesn't have {status_column} column")
        return False

    # Aktuální status _sharpen
    current_sharpen_status = sharpen_record[status_column]

    # Aktualizuj pouze pokud má status "záložní"
    if current_sharpen_status != STATUS_BACKUP:
        logging.debug(f"_sharpen {sharpen_record.get(COL_FILE)} has status '{current_sharpen_status}', not '{STATUS_BACKUP}', skipping")
        return False

    # Urči nový status _sharpen na základě originálu
    new_sharpen_status = None
    if new_original_status == STATUS_APPROVED:
        # Originál schválen → _sharpen není potřeba
        new_sharpen_status = STATUS_UNUSED
        logging.info(f"Original {original_filename} approved -> setting _sharpen to '{STATUS_UNUSED}' for {bank}")
    elif new_original_status == STATUS_REJECTED:
        # Originál zamítnut → použij _sharpen místo něj
        new_sharpen_status = STATUS_PREPARED
        logging.info(f"Original {original_filename} rejected -> setting _sharpen to '{STATUS_PREPARED}' for {bank}")
    elif new_original_status == STATUS_MAYBE:
        # "Možná" - nedělej nic, ponech "záložní"
        logging.debug(f"Original {original_filename} status is '{STATUS_MAYBE}', keeping _sharpen as '{STATUS_BACKUP}'")
        return False

    # Aplikuj změnu
    if new_sharpen_status:
        sharpen_record[status_column] = new_sharpen_status
        logging.info(f"SHARPEN_STATUS_CHANGE: {sharpen_record.get(COL_FILE)} : {bank} : {current_sharpen_status} -> {new_sharpen_status}")
        return True

    return False


def is_edited_photo(record: Dict[str, str]) -> bool:
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


def filter_records_by_edit_type(records: List[Dict[str, str]], include_edited: bool = False) -> List[Dict[str, str]]:
    """
    Filter records based on whether they are edited photos.

    Logic:
    - _sharpen files: ALWAYS excluded (managed automatically via update_sharpen_status)
    - Other edited photos (with edit tags _bw, _negative, _misty, _blurred): included only if include_edited=True
    - Original photos (without edit tags): always included

    Note: Alternative FORMATS (PNG, TIF) are not in MediaCSV at all, so no filtering needed.

    Args:
        records: List of CSV records
        include_edited: If True, include edited photos with edit tags (except _sharpen)

    Returns:
        Filtered list of records
    """
    if not records:
        return []

    filtered = []
    excluded_sharpen = 0
    excluded_edited = 0

    for record in records:
        filename = record.get(COL_FILE, '')
        if not filename:
            filtered.append(record)
            continue

        filename_lower = filename.lower()
        name_without_ext = os.path.splitext(filename_lower)[0]

        # ALWAYS exclude _sharpen files (they're managed automatically)
        if name_without_ext.endswith('_sharpen'):
            excluded_sharpen += 1
            logging.debug(f"Excluding _sharpen file (always excluded): {filename}")
            continue

        # Exclude other edited photos if include_edited=False
        if not include_edited and is_edited_photo(record):
            excluded_edited += 1
            logging.debug(f"Excluding edited photo: {filename}")
            continue

        filtered.append(record)

    logging.info(f"Filtered {len(filtered)} records from {len(records)} total "
                f"(excluded {excluded_sharpen} _sharpen files, {excluded_edited} edited photos)")

    return filtered



