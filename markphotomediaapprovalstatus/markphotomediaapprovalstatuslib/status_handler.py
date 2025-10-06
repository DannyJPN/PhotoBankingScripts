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
    COL_ORIGINAL,
    ORIGINAL_YES,
    EDIT_SHARPEN
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
        logging.info(f"Original {original_filename} approved → setting _sharpen to '{STATUS_UNUSED}' for {bank}")
    elif new_original_status == STATUS_REJECTED:
        # Originál zamítnut → použij _sharpen místo něj
        new_sharpen_status = STATUS_PREPARED
        logging.info(f"Original {original_filename} rejected → setting _sharpen to '{STATUS_PREPARED}' for {bank}")
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



