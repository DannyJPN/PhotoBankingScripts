"""
Helper functions for media file processing - adapted for approval workflow.
"""

import os
import logging
from typing import List, Dict
from markphotomediaapprovalstatuslib.constants import STATUS_COLUMN_KEYWORD
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
    Process approval records sequentially using MediaViewer GUI.
    
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
    processed_count = 0
    
    logging.info(f"Processing {len(filtered_data)} records sequentially")
    
    for record in filtered_data:
        processed_count += 1
        logging.info(f"Processing record {processed_count}/{len(filtered_data)}")
        
        # Get file info
        file_path = record.get('Cesta', '')
        file_name = record.get('Soubor', 'Unknown')
        
        if not file_path:
            logging.warning(f"No file path provided for {file_name}, skipping")
            continue
            
        # Check if file exists using centralized logging instead of file operations
        if not os.path.exists(file_path):
            logging.warning(f"File not found: {file_path}, skipping {file_name}")
            continue
        
        # Show media viewer and wait for decisions (no timeout, sequential processing)
        decisions = {}
        
        def completion_callback(user_decisions):
            nonlocal decisions
            decisions = user_decisions
            
        try:
            # Import here to avoid circular import
            from markphotomediaapprovalstatuslib.media_viewer import show_media_viewer
            show_media_viewer(file_path, record, completion_callback)
            
            # Apply decisions to the record
            if decisions:
                file_changed = False
                for bank, decision in decisions.items():
                    status_column = f"{bank} {STATUS_COLUMN_KEYWORD}"
                    if status_column in record:
                        old_value = record[status_column]
                        record[status_column] = decision
                        changes_made = True
                        file_changed = True
                        
                        # Log the change using centralized logging only
                        logging.info(f"APPROVAL_CHANGE: {file_name} : {bank} : {old_value} -> {decision}")
                
                # Save immediately after processing each file with changes

                if file_changed:
                    try:
                        save_csv_with_backup(data, csv_path)
                        logging.info(f"Saved changes after processing {file_name}")
                    except Exception as e:
                        logging.error(f"Failed to save changes after processing {file_name}: {e}")
                        # Continue processing even if save fails
                        
        except Exception as e:
            logging.error(f"Error processing {file_name}: {e}")
            continue
    
    logging.info(f"Completed processing {processed_count} records, changes made: {changes_made}")
    return changes_made