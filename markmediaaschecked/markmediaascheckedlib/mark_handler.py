"""
Handler module for marking media as checked in CSV files.
"""

import logging

from markmediaascheckedlib.constants import STATUS_CHECKED, STATUS_COLUMN_KEYWORD, STATUS_READY


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
    status_columns = [col for col in first_record.keys() if STATUS_COLUMN_KEYWORD.lower() in col.lower()]

    logging.info(f"Found {len(status_columns)} status columns: {', '.join(status_columns)}")
    return status_columns


def filter_records_by_status(records: list[dict], status_columns: list[str], status_value: str) -> list[dict]:
    """
    Vrátí seznam záznamů, kde alespoň jeden statusový sloupec obsahuje zadanou hodnotu status_value.
    Generícká metoda, která umí vyhledat záznamy s libovolným statusem.

    Args:
        records: Seznam záznamů k prohledání
        status_columns: Seznam názvů sloupců obsahujících status
        status_value: Hodnota statusu, kterou hledáme

    Returns:
        Seznam záznamů, kde alespoň jeden statusový sloupec obsahuje status_value
    """
    if not records:
        logging.warning("No records provided to filter")
        return []

    if not status_columns:
        logging.warning("No status columns provided for filtering")
        return []

    filtered_records = []
    for record in records:
        for col in status_columns:
            if col in record and record[col] == status_value:
                filtered_records.append(record)
                break  # Once we find one matching status, we can add the record and move on

    logging.info(f"Found {len(filtered_records)} records with status '{status_value}'")
    return filtered_records


def filter_ready_records(records: list[dict], status_columns: list[str]) -> list[dict]:
    """
    Vrátí seznam záznamů, kde alespoň jeden statusový sloupec obsahuje hodnotu STATUS_READY.
    Používá generickou metodu filter_records_by_status.
    """
    return filter_records_by_status(records, status_columns, STATUS_READY)


def update_status_values(records: list[dict], status_columns: list[str], old_status: str, new_status: str) -> int:
    """
    V každém statusovém sloupci v každém záznamu nahradí old_status → new_status.
    Generícká metoda, která umí nahradit libovolný status za jiný.
    Vypisuje počet změn pro každou fotobanku (status sloupec) a v debug módu také u kterých souborů.

    Args:
        records: Seznam záznamů k aktualizaci
        status_columns: Seznam názvů sloupců obsahujících status
        old_status: Původní hodnota statusu, kterou chceme nahradit
        new_status: Nová hodnota statusu

    Returns:
        Počet provedených změn
    """
    if not records:
        logging.warning("No records provided to update")
        return 0

    if not status_columns:
        logging.warning("No status columns provided for updating")
        return 0

    # Dictionary to track changes per photo bank (status column)
    changes_per_column = dict.fromkeys(status_columns, 0)

    # Dictionary to track which files were changed for each photo bank
    changed_files_per_column = {col: [] for col in status_columns}

    total_change_count = 0
    for record in records:
        for col in status_columns:
            if col in record and record[col] == old_status:
                record[col] = new_status
                changes_per_column[col] += 1
                total_change_count += 1

                # If in debug mode and the record has a name/filename field, track it
                if logging.getLogger().level <= logging.DEBUG and "name" in record:
                    changed_files_per_column[col].append(record["name"])

    # Log changes for each photo bank
    for col in status_columns:
        if changes_per_column[col] > 0:
            logging.info(
                f"Updated {changes_per_column[col]} status values from '{old_status}' to '{new_status}' in {col}"
            )

            # In debug mode, also log which files were changed
            if logging.getLogger().level <= logging.DEBUG and changed_files_per_column[col]:
                files_str = ", ".join(changed_files_per_column[col])
                logging.debug(f"Files changed in {col}: {files_str}")

    logging.info(f"Total: Updated {total_change_count} status values from '{old_status}' to '{new_status}'")
    return total_change_count


def update_statuses(records: list[dict], status_columns: list[str]) -> int:
    """
    V každém statusovém sloupci v každém záznamu nahradí STATUS_READY → STATUS_CHECKED.
    Používá generickou metodu update_status_values.

    Returns:
        Počet provedených změn
    """
    return update_status_values(records, status_columns, STATUS_READY, STATUS_CHECKED)
