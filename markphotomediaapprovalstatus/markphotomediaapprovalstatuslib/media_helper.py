"""
Helper functions for media file processing - adapted for approval workflow.
"""

import os
import logging
from typing import List, Dict
from markphotomediaapprovalstatuslib.constants import (
    BANKS,
    STATUS_COLUMN_KEYWORD,
    STATUS_CHECKED
)
from markphotomediaapprovalstatuslib.status_handler import (
    filter_records_by_bank_status,
    update_sharpen_status
)
from shared.file_operations import save_csv_with_backup


def is_video_file(file_path: str) -> bool:
    """Check if file is a video based on extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm', '.m4v'}
    return ext in video_extensions


def is_jpg_file(file_path: str) -> bool:
    """Check if file is JPG/JPEG."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    return ext in ['.jpg', '.jpeg']


def is_media_file(file_path: str) -> bool:
    """Check if file is a multimedia file based on extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower().lstrip('.')
    
    # All supported media extensions
    media_extensions = {
        # Images
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp',
        'raw', 'arw', 'cr2', 'nef', 'dng', 'orf', 'rw2', 'pef', 'srw',
        # Videos  
        'mp4', 'avi', 'mov', 'wmv', 'mkv', 'flv', 'webm', 'm4v', 'm2ts', 'mts',
        # Vector graphics
        'svg', 'ai', 'eps', 'cdr', 'pdf'
    }
    
    return ext in media_extensions


def process_approval_records(
    data: List[Dict[str, str]],
    filtered_data: List[Dict[str, str]],
    csv_path: str,
    batch_action: str = ""
) -> bool:
    """
    Process approval records bank-by-bank, file-by-file using MediaViewer GUI.

    Workflow:
        FOR each bank (outer loop):
            FOR each file with "kontrolováno" for that bank (inner loop):
                Show GUI with single bank controls
                Collect decision for that bank
                Save immediately

    Args:
        data: Complete CSV data (for modifications)
        filtered_data: Records with STATUS_CHECKED status to process
        csv_path: Path to CSV file for immediate saving after each change

    Returns:
        True if any changes were made, False otherwise
    """
    if not filtered_data:
        logging.info("No records to process")
        return False

    changes_made = False
    total_banks = len(BANKS)

    logging.info(f"Starting bank-first iteration across {total_banks} banks")

    # OUTER LOOP: Iterate through BANKS
    for bank_index, bank in enumerate(BANKS, start=1):
        logging.info(f"=== Processing bank {bank_index}/{total_banks}: {bank} ===")

        # Filter records for THIS bank only
        bank_records = filter_records_by_bank_status(filtered_data, bank, STATUS_CHECKED)

        if not bank_records:
            logging.info(f"No records with '{STATUS_CHECKED}' status for {bank}, skipping")
            continue

        logging.info(f"Found {len(bank_records)} records for {bank}")

        # INNER LOOP: Iterate through FILES for this bank
        for file_index, record in enumerate(bank_records, start=1):
            file_path = record.get('Cesta', '')
            file_name = record.get('Soubor', 'Unknown')

            logging.info(f"Processing {bank} - file {file_index}/{len(bank_records)}: {file_name}")

            if not file_path:
                logging.warning(f"No file path provided for {file_name}, skipping")
                continue

            # Check if file exists
            if not os.path.exists(file_path):
                logging.warning(f"File not found: {file_path}, skipping {file_name}")
                continue

            if batch_action:
                decision = _map_batch_action(batch_action)
                _apply_decision(record, data, bank, decision, file_name, csv_path)
                changes_made = True
                continue

            # Show viewer for THIS BANK ONLY
            decision = None

            def completion_callback(user_decision):
                nonlocal decision
                decision = user_decision

            try:
                # Import here to avoid circular import
                from markphotomediaapprovalstatuslib.media_viewer import show_media_viewer
                show_media_viewer(file_path, record, completion_callback, target_bank=bank)

                if decision:
                    _apply_decision(record, data, bank, decision, file_name, csv_path)
                    changes_made = True

            except Exception as e:
                logging.error(f"Error processing {file_name} for {bank}: {e}")
                continue

        logging.info(f"Completed bank {bank}")

    logging.info(f"=== Completed all {total_banks} banks, changes made: {changes_made} ===")
    return changes_made


def _map_batch_action(batch_action: str) -> str:
    """
    Map batch action to status value.
    """
    if batch_action == "approve":
        return STATUS_APPROVED
    if batch_action == "reject":
        return STATUS_REJECTED
    return STATUS_MAYBE


def _apply_decision(
    record: Dict[str, str],
    all_records: List[Dict[str, str]],
    bank: str,
    decision: str,
    file_name: str,
    csv_path: str
) -> None:
    """
    Apply approval decision and save changes.
    """
    status_column = f"{bank} {STATUS_COLUMN_KEYWORD}"
    if status_column in record:
        old_value = record[status_column]
        record[status_column] = decision
        logging.info(f"APPROVAL_CHANGE: {file_name} : {bank} : {old_value} -> {decision}")
        update_sharpen_status(record, all_records, bank, decision)
        try:
            save_csv_with_backup(all_records, csv_path)
            logging.info(f"Saved changes after processing {file_name} for {bank}")
        except Exception as e:
            logging.error(f"Failed to save changes after processing {file_name}: {e}")
