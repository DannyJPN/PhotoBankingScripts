"""
Path builder for calculating target paths for media files.
"""

import os
from datetime import datetime


def build_target_path(base_folder: str, media_type: str, extension: str, 
                     category: str, date: datetime, camera_name: str, 
                     is_edited: bool = False, edit_type: str = "") -> str:
    """
    Build target path for a media file.
    
    Args:
        base_folder: Base target folder
        media_type: Type of media (Foto/Video)
        extension: File extension
        category: Category name
        date: Creation date
        camera_name: Camera name
        is_edited: Whether file is edited
        edit_type: Type of edit
        
    Returns:
        Target path for the file
    """
    year = date.strftime("%Y")
    month = date.strftime("%m")
    
    path = os.path.join(
        base_folder,
        media_type,
        extension.upper() if extension else "UNKNOWN",
        category,
        year,
        month,
        camera_name
    )
    
    return path


def ensure_unique_path(target_path: str) -> str:
    """
    Ensure the target path is unique by adding a counter if needed.
    
    Args:
        target_path: Original target path
        
    Returns:
        Unique target path
    """
    if not os.path.exists(target_path):
        return target_path
    
    directory = os.path.dirname(target_path)
    filename = os.path.basename(target_path)
    name, ext = os.path.splitext(filename)
    
    counter = 1
    while True:
        new_filename = f"{name}_{counter:03d}{ext}"
        new_path = os.path.join(directory, new_filename)
        if not os.path.exists(new_path):
            return new_path
        counter += 1

