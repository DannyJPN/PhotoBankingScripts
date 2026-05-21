"""
Helper functions for media file processing - adapted for approval workflow.
"""

import os
import logging
from typing import List, Dict
from markphotomediaapprovalstatusautolib.constants import (
    BANKS,
    STATUS_COLUMN_KEYWORD,
    STATUS_CHECKED
)
from markphotomediaapprovalstatusautolib.status_handler import (
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


def process_approval_records(data: List[Dict[str, str]], filtered_data: List[Dict[str, str]], csv_path: str) -> bool:
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

    logging.info("Starting bank-first iteration across %d banks", total_banks)

    # OUTER LOOP: Iterate through BANKS
    for bank_index, bank in enumerate(BANKS, start=1):
        logging.info("=== Processing bank %d/%d: %s ===", bank_index, total_banks, bank)

        # Filter records for THIS bank only
        bank_records = filter_records_by_bank_status(filtered_data, bank, STATUS_CHECKED)

        if not bank_records:
            logging.info("No records with '%s' status for %s, skipping", STATUS_CHECKED, bank)
            continue

        logging.info("Found %d records for %s", len(bank_records), bank)

        # INNER LOOP: Iterate through FILES for this bank
        for file_index, record in enumerate(bank_records, start=1):
            file_path = record.get('Cesta', '')
            file_name = record.get('Soubor', 'Unknown')

            logging.info("Processing %s - file %d/%d: %s", bank, file_index, len(bank_records), file_name)

            if not file_path:
                logging.warning("No file path provided for %s, skipping", file_name)
                continue

            # Check if file exists
            if not os.path.exists(file_path):
                logging.warning("File not found: %s, skipping %s", file_path, file_name)
                continue

            # Show viewer for THIS BANK ONLY
            decision = None

            def completion_callback(user_decision):
                nonlocal decision
                decision = user_decision

            try:
                # Import here to avoid circular import
                from markphotomediaapprovalstatusautolib.media_viewer import show_media_viewer
                show_media_viewer(file_path, record, completion_callback, target_bank=bank)

                # Apply decision for THIS bank
                if decision:
                    status_column = f"{bank} {STATUS_COLUMN_KEYWORD}"
                    if status_column in record:
                        old_value = record[status_column]
                        record[status_column] = decision
                        changes_made = True

                        logging.info("APPROVAL_CHANGE: %s : %s : %s -> %s", file_name, bank, old_value, decision)

                        # Update _sharpen status if needed
                        sharpen_changed = update_sharpen_status(record, data, bank, decision)

                        # Save immediately after each file
                        try:
                            save_csv_with_backup(data, csv_path)
                            logging.info("Saved changes after processing %s for %s", file_name, bank)
                        except Exception as e:
                            logging.error("Failed to save changes after processing %s: %s", file_name, e)

            except Exception as e:
                logging.error("Error processing %s for %s: %s", file_name, bank, e)
                continue

        logging.info("Completed bank %s", bank)

    logging.info("=== Completed all %d banks, changes made: %s ===", total_banks, changes_made)
    return changes_made