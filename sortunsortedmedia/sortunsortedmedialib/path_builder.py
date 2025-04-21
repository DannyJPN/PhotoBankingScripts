"""
Path builder for calculating target paths for media files.
"""

import os
import logging
from datetime import datetime
from typing import Optional

from sortunsortedmedialib.constants import FOLDER_STRUCTURE, DATE_FORMAT

def build_target_path(
    base_folder: str,
    media_type: str,
    extension: str,
    category: str,
    date: datetime,
    camera_name: str,
    is_edited: bool,
    edit_type: Optional[str] = None
) -> str:
    """
    Builds the target path for a media file.
    
    Args:
        base_folder: Base target folder
        media_type: Type of media (Foto, Video)
        extension: File extension (without dot)
        category: Media category
        date: Creation date
        camera_name: Camera name
        is_edited: Whether the file is edited
        edit_type: Type of edit (if is_edited is True)
        
    Returns:
        Full target path including filename
    """
    # Format date components
    year = date.strftime("%Y")
    month = date.strftime("%m")
    day = date.strftime("%d")
    date_str = date.strftime(DATE_FORMAT)
    
    # Sanitize category and camera name for use in filenames
    category = category.replace(" ", "_").replace("/", "-")
    camera_name = camera_name.replace(" ", "_").replace("/", "-")
    
    # Determine the folder structure to use
    if is_edited:
        structure_key = "Edited"
    else:
        structure_key = media_type
    
    # Get the folder structure format
    if structure_key in FOLDER_STRUCTURE:
        folder_format = FOLDER_STRUCTURE[structure_key]
    else:
        logging.warning(f"Unknown structure key: {structure_key}, using Foto structure")
        folder_format = FOLDER_STRUCTURE["Foto"]
    
    # Format the folder path
    folder_path = folder_format.format(
        year=year,
        month=month,
        day=day,
        date=date_str,
        category=category,
        camera=camera_name,
        edit_type=edit_type if edit_type else "Edited"
    )
    
    # Combine with base folder
    full_folder_path = os.path.join(base_folder, folder_path)
    
    # Generate a unique filename
    base_filename = f"{date.strftime('%Y%m%d')}_{category}_{camera_name}"
    if is_edited and edit_type:
        base_filename += f"_{edit_type}"
    
    # Add extension
    if not extension.startswith('.'):
        extension = f".{extension}"
    filename = f"{base_filename}{extension}"
    
    # Combine folder path and filename
    full_path = os.path.join(full_folder_path, filename)
    
    logging.debug(f"Built target path: {full_path}")
    return full_path

def ensure_unique_path(target_path: str) -> str:
    """
    Ensures the target path is unique by adding a numeric suffix if needed.
    
    Args:
        target_path: The initial target path
        
    Returns:
        A unique path that doesn't exist yet
    """
    if not os.path.exists(target_path):
        return target_path
    
    # Split path into directory, base filename, and extension
    directory = os.path.dirname(target_path)
    filename = os.path.basename(target_path)
    name, ext = os.path.splitext(filename)
    
    # Try adding numeric suffixes until we find a unique path
    counter = 1
    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_path = os.path.join(directory, new_filename)
        
        if not os.path.exists(new_path):
            logging.debug(f"Generated unique path: {new_path}")
            return new_path
        
        counter += 1
