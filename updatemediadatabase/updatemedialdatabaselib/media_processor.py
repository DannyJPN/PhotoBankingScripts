"""
Module for processing media files.
Contains the main logic for processing individual media files.
"""
import os
import logging
from typing import Dict, List, Optional, Any

from updatemedialdatabaselib.constants import (
    PHOTO_EXTENSIONS,
    VIDEO_EXTENSIONS,
    TYPE_PHOTO,
    TYPE_VIDEO,
    TYPE_EDITED_PHOTO,
    TYPE_EDITED_VIDEO,
    COLUMN_FILENAME,
    COLUMN_PATH,
    COLUMN_ORIGINAL
)
from updatemedialdatabaselib.edit_utils import (
    is_edited_file,
    get_edit_type,
    get_original_filename,
    update_metadata_for_edit
)
from updatemedialdatabaselib.photo_analyzer import (
    extract_metadata,
    validate_against_limits
)

def find_original_file(edited_filename: str, database: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Find the original file record for an edited file.
    
    Args:
        edited_filename: The filename of the edited file
        database: The database of media files
        
    Returns:
        The original file record or None if not found
    """
    # Try to extract original filename from edited filename
    original_filename = get_original_filename(edited_filename)
    if not original_filename:
        logging.debug(f"Could not determine original filename for: {edited_filename}")
        return None
    
    # Search for original file in database
    for record in database:
        if record.get(COLUMN_FILENAME) == original_filename:
            logging.info(f"Found original file for {edited_filename}: {original_filename}")
            return record
    
    logging.debug(f"Original file not found in database: {original_filename}")
    return None

def determine_media_type(file_path: str, is_edited: bool) -> str:
    """
    Determine the media type based on file extension and edit status.
    
    Args:
        file_path: Path to the media file
        is_edited: Whether the file is edited
        
    Returns:
        Media type (TYPE_PHOTO, TYPE_VIDEO, TYPE_EDITED_PHOTO, TYPE_EDITED_VIDEO)
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in PHOTO_EXTENSIONS:
        return TYPE_EDITED_PHOTO if is_edited else TYPE_PHOTO
    elif ext in VIDEO_EXTENSIONS:
        return TYPE_EDITED_VIDEO if is_edited else TYPE_VIDEO
    else:
        return "Unknown"

def is_file_in_database(file_path: str, database: List[Dict[str, str]]) -> bool:
    """
    Check if a file is already in the database.
    
    Args:
        file_path: Path to the file
        database: The database of media files
        
    Returns:
        True if the file is in the database, False otherwise
    """
    filename = os.path.basename(file_path)
    path = os.path.dirname(file_path)
    
    for record in database:
        if (record.get(COLUMN_FILENAME) == filename and 
            record.get(COLUMN_PATH) == path):
            return True
    
    return False

def process_media_file(
    file_path: str, 
    database: List[Dict[str, str]], 
    limits: List[Dict[str, str]], 
    exiftool_path: str
) -> Optional[Dict[str, Any]]:
    """
    Process a media file and create a database record.
    
    Args:
        file_path: Path to the media file
        database: The database of media files
        limits: List of dictionaries with limits for each photo bank
        exiftool_path: Path to the ExifTool executable
        
    Returns:
        A new database record or None if the file should be skipped
    """
    # Skip if file is already in database
    if is_file_in_database(file_path, database):
        logging.debug(f"File already in database, skipping: {file_path}")
        return None
    
    # Extract metadata
    metadata = extract_metadata(file_path, exiftool_path)
    if not metadata:
        logging.warning(f"Could not extract metadata, skipping: {file_path}")
        return None
    
    # Check if file is edited
    filename = os.path.basename(file_path)
    is_edited = is_edited_file(filename)
    
    # Determine media type
    media_type = determine_media_type(file_path, is_edited)
    metadata["Type"] = media_type
    
    # If edited, find original and update metadata
    if is_edited:
        edit_type = get_edit_type(filename)
        if edit_type:
            # Find original file in database
            original_record = find_original_file(filename, database)
            if original_record:
                # Copy relevant metadata from original
                for field in ["Title", "Description", "Keywords"]:
                    if field in original_record and original_record[field]:
                        metadata[field] = original_record[field]
                
                # Add reference to original
                metadata[COLUMN_ORIGINAL] = original_record.get(COLUMN_FILENAME, "")
            
            # Update metadata for edit type
            metadata = update_metadata_for_edit(metadata, edit_type)
    
    # Validate against limits
    validation_results = validate_against_limits(metadata, limits)
    
    # Add validation results to metadata
    for bank, valid in validation_results.items():
        metadata[f"Valid_{bank}"] = "Yes" if valid else "No"
    
    logging.info(f"Processed media file: {file_path}")
    return metadata
