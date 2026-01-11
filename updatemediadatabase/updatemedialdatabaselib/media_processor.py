"""
Module for processing media files.
Contains the main logic for processing individual media files.
"""
import os
import logging
from typing import Dict, List, Optional, Any

from updatemedialdatabaselib.constants import (
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    TYPE_PHOTO,
    TYPE_VIDEO,
    TYPE_EDITED_PHOTO,
    TYPE_EDITED_VIDEO,
    COLUMN_FILENAME,
    COLUMN_PATH,
    COLUMN_ORIGINAL,
    COLUMN_TITLE,
    COLUMN_DESCRIPTION,
    COLUMN_DATE_PREPARED,
    COLUMN_WIDTH,
    COLUMN_HEIGHT,
    COLUMN_RESOLUTION,
    COLUMN_KEYWORDS,
    COLUMN_CATEGORIES,
    COLUMN_DATE_CREATED,
    COLUMN_SHUTTERSTOCK_STATUS,
    COLUMN_BIGSTOCKPHOTO_STATUS,
    COLUMN_ADOBESTOCK_STATUS,
    COLUMN_DEPOSITPHOTOS_STATUS,
    COLUMN_123RF_STATUS,
    COLUMN_ALAMY_STATUS,
    COLUMN_GETTYIMAGES_STATUS,
    COLUMN_COLOURBOX_STATUS,
    COLUMN_DREAMSTIME_STATUS,
    COLUMN_CANSTOCKPHOTO_STATUS,
    COLUMN_POND5_STATUS,
    COLUMN_PIXTA_STATUS,
    COLUMN_FREEPIK_STATUS,
    COLUMN_VECTEEZY_STATUS,
    COLUMN_STORYBLOCKS_STATUS,
    COLUMN_ENVATO_STATUS,
    COLUMN_500PX_STATUS,
    COLUMN_MOSTPHOTOS_STATUS,
    COLUMN_SHUTTERSTOCK_CATEGORY,
    COLUMN_BIGSTOCKPHOTO_CATEGORY,
    COLUMN_ADOBESTOCK_CATEGORY,
    COLUMN_DEPOSITPHOTOS_CATEGORY,
    COLUMN_123RF_CATEGORY,
    COLUMN_ALAMY_CATEGORY,
    COLUMN_GETTYIMAGES_CATEGORY,
    COLUMN_COLOURBOX_CATEGORY,
    COLUMN_DREAMSTIME_CATEGORY,
    COLUMN_CANSTOCKPHOTO_CATEGORY,
    COLUMN_POND5_CATEGORY,
    COLUMN_PIXTA_CATEGORY,
    COLUMN_FREEPIK_CATEGORY,
    COLUMN_VECTEEZY_CATEGORY,
    COLUMN_STORYBLOCKS_CATEGORY,
    COLUMN_ENVATO_CATEGORY,
    COLUMN_500PX_CATEGORY,
    COLUMN_MOSTPHOTOS_CATEGORY
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

def get_bank_status(bank_name: str, is_valid: bool, metadata: Dict[str, Any]) -> str:
    """
    Get the status text for a photo bank based on validation result.

    Args:
        bank_name: Name of the photo bank
        is_valid: Whether the file meets the bank's requirements
        metadata: File metadata including dimensions

    Returns:
        Status text in Czech
    """
    if is_valid:
        return "nezpracováno"

    # Check if rejection is due to size limits
    width = metadata.get("Width")
    height = metadata.get("Height")
    if width and height:
        return "zamítnuto - velikost"

    return "zamítnuto - velikost"

def extract_category_from_path(file_path: str) -> str:
    """
    Extract category from file path - name of folder 4 levels up from the file.

    Args:
        file_path: Full path to the file

    Returns:
        Category name (folder name 4 levels up) or empty string if not found
    """
    try:
        # Normalize path separators
        normalized_path = os.path.normpath(file_path)
        path_parts = normalized_path.split(os.sep)

        # Need at least 5 parts to have 4 levels up (file + 4 parent directories)
        if len(path_parts) >= 5:
            category = path_parts[-5]  # 4 levels up from file
            return category
        else:
            logging.debug(f"Path too short to extract category (4 levels up): {file_path}")
            return ""
    except Exception as e:
        logging.warning(f"Error extracting category from path {file_path}: {e}")
        return ""

def calculate_resolution_mpx(width: int, height: int) -> str:
    """
    Calculate resolution in megapixels from width and height.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Resolution in Mpx format (e.g., "12.5")
    """
    if width and height:
        mpx = (width * height) / 1_000_000
        return f"{mpx:.1f}"
    return ""

def create_database_record(metadata: Dict[str, Any], validation_results: Dict[str, bool]) -> Dict[str, str]:
    """
    Create a database record with proper Czech column names matching existing database structure and order.

    Args:
        metadata: Extracted metadata from file
        validation_results: Validation results for each photo bank

    Returns:
        Database record with Czech column names in exact order
    """
    from collections import OrderedDict

    # Extract category from file path (4 levels up)
    # Path in metadata already contains the full path to the file
    file_path = metadata.get("Path", "")
    category = extract_category_from_path(file_path)

    # Get resolution in Mpx - use from metadata if available, otherwise calculate
    resolution_mpx = metadata.get("Resolution", "")
    if not resolution_mpx:
        width = metadata.get("Width")
        height = metadata.get("Height")
        resolution_mpx = calculate_resolution_mpx(width, height) if width and height else ""

    # Create record with exact column order matching existing database
    record = OrderedDict([
        (COLUMN_FILENAME, metadata.get("Filename", "")),
        (COLUMN_TITLE, metadata.get("Title", "")),
        (COLUMN_DESCRIPTION, metadata.get("Description", "")),
        (COLUMN_DATE_PREPARED, ""),  # To be filled by preparemediafile
        (COLUMN_WIDTH, str(metadata.get("Width", ""))),
        (COLUMN_HEIGHT, str(metadata.get("Height", ""))),
        (COLUMN_RESOLUTION, resolution_mpx),
        (COLUMN_KEYWORDS, metadata.get("Keywords", "")),
        (COLUMN_CATEGORIES, category),
        (COLUMN_DATE_CREATED, metadata.get("Date", "")),
        (COLUMN_SHUTTERSTOCK_STATUS, get_bank_status("ShutterStock", validation_results.get("ShutterStock", True), metadata)),
        (COLUMN_BIGSTOCKPHOTO_STATUS, get_bank_status("BigStockPhoto", validation_results.get("BigStockPhoto", True), metadata)),
        (COLUMN_ADOBESTOCK_STATUS, get_bank_status("AdobeStock", validation_results.get("AdobeStock", True), metadata)),
        (COLUMN_DEPOSITPHOTOS_STATUS, get_bank_status("DepositPhotos", validation_results.get("DepositPhotos", True), metadata)),
        (COLUMN_123RF_STATUS, get_bank_status("123RF", validation_results.get("123RF", True), metadata)),
        (COLUMN_ALAMY_STATUS, get_bank_status("Alamy", validation_results.get("Alamy", True), metadata)),
        (COLUMN_GETTYIMAGES_STATUS, get_bank_status("GettyImages", validation_results.get("GettyImages", True), metadata)),
        (COLUMN_COLOURBOX_STATUS, get_bank_status("ColourBox", validation_results.get("ColourBox", True), metadata)),
        (COLUMN_DREAMSTIME_STATUS, get_bank_status("Dreamstime", validation_results.get("Dreamstime", True), metadata)),
        (COLUMN_CANSTOCKPHOTO_STATUS, get_bank_status("CanStockPhoto", validation_results.get("CanStockPhoto", True), metadata)),
        (COLUMN_POND5_STATUS, get_bank_status("Pond5", validation_results.get("Pond5", True), metadata)),
        # New banks
        (COLUMN_PIXTA_STATUS, get_bank_status("Pixta", validation_results.get("Pixta", True), metadata)),
        (COLUMN_FREEPIK_STATUS, get_bank_status("Freepik", validation_results.get("Freepik", True), metadata)),
        (COLUMN_VECTEEZY_STATUS, get_bank_status("Vecteezy", validation_results.get("Vecteezy", True), metadata)),
        (COLUMN_STORYBLOCKS_STATUS, get_bank_status("StoryBlocks", validation_results.get("StoryBlocks", True), metadata)),
        (COLUMN_ENVATO_STATUS, get_bank_status("Envato", validation_results.get("Envato", True), metadata)),
        (COLUMN_500PX_STATUS, get_bank_status("500px", validation_results.get("500px", True), metadata)),
        (COLUMN_MOSTPHOTOS_STATUS, get_bank_status("MostPhotos", validation_results.get("MostPhotos", True), metadata)),
        (COLUMN_SHUTTERSTOCK_CATEGORY, ""),
        (COLUMN_BIGSTOCKPHOTO_CATEGORY, ""),
        (COLUMN_ADOBESTOCK_CATEGORY, ""),
        (COLUMN_DEPOSITPHOTOS_CATEGORY, ""),
        (COLUMN_123RF_CATEGORY, ""),
        (COLUMN_ALAMY_CATEGORY, ""),
        (COLUMN_GETTYIMAGES_CATEGORY, ""),
        (COLUMN_COLOURBOX_CATEGORY, ""),
        (COLUMN_DREAMSTIME_CATEGORY, ""),
        (COLUMN_CANSTOCKPHOTO_CATEGORY, ""),
        (COLUMN_POND5_CATEGORY, ""),
        # New banks
        (COLUMN_PIXTA_CATEGORY, ""),
        (COLUMN_FREEPIK_CATEGORY, ""),
        (COLUMN_VECTEEZY_CATEGORY, ""),
        (COLUMN_STORYBLOCKS_CATEGORY, ""),
        (COLUMN_ENVATO_CATEGORY, ""),
        (COLUMN_500PX_CATEGORY, ""),
        (COLUMN_MOSTPHOTOS_CATEGORY, ""),
        (COLUMN_ORIGINAL, metadata.get("Original", "")),
        (COLUMN_PATH, metadata.get("Path", ""))
    ])

    return record

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
            logging.debug(f"Found original file for {edited_filename}: {original_filename}")
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
    
    if ext in IMAGE_EXTENSIONS:
        return TYPE_EDITED_PHOTO if is_edited else TYPE_PHOTO
    elif ext in VIDEO_EXTENSIONS:
        return TYPE_EDITED_VIDEO if is_edited else TYPE_VIDEO
    else:
        return "Unknown"

def is_file_in_database(file_path: str, existing_filenames: set) -> bool:
    """
    Check if a file is already in the database by filename only.

    Args:
        file_path: Path to the file
        existing_filenames: Set of existing filenames in database

    Returns:
        True if the file is in the database, False otherwise
    """
    filename = os.path.basename(file_path)
    return filename in existing_filenames

def process_media_file(
    file_path: str,
    database: List[Dict[str, str]],
    limits: List[Dict[str, str]],
    exiftool_path: str,
    existing_filenames: set
) -> Optional[Dict[str, Any]]:
    """
    Process a media file and create a database record.

    Args:
        file_path: Path to the media file
        database: The database of media files
        limits: List of dictionaries with limits for each photo bank
        exiftool_path: Path to the ExifTool executable
        existing_filenames: Set of existing filenames for efficient lookup

    Returns:
        A new database record or None if the file should be skipped
    """
    # Skip if file is already in database
    if is_file_in_database(file_path, existing_filenames):
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

    # Create database record with proper Czech column structure
    database_record = create_database_record(metadata, validation_results)

    logging.debug(f"Processed media file: {file_path}")
    return database_record
