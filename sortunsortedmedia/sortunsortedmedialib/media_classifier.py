"""
Media classifier module for detecting media origins, edits, and extensions.
"""

import os
import re
import logging
from typing import Optional, Tuple

from sortunsortedmedialib.constants import EDITED_TAGS, CAMERA_REGEXES, EXTENSION_TYPES

def is_edited(filename: str) -> bool:
    """
    Determines if a file has been edited based on its filename.
    
    Args:
        filename: The filename to check
        
    Returns:
        True if the filename contains any edit tags, False otherwise
    """
    basename = os.path.basename(filename)
    name, _ = os.path.splitext(basename)
    
    for tag in EDITED_TAGS.keys():
        if tag.lower() in name.lower():
            logging.debug(f"File {filename} identified as edited (tag: {tag})")
            return True
    
    return False

def get_edit_type(filename: str) -> Optional[str]:
    """
    Returns the type of edit for an edited file.
    
    Args:
        filename: The filename to check
        
    Returns:
        The edit type description or None if not edited
    """
    if not is_edited(filename):
        return None
        
    basename = os.path.basename(filename)
    name, _ = os.path.splitext(basename)
    
    for tag, description in EDITED_TAGS.items():
        if tag.lower() in name.lower():
            return description
    
    return "Edited"  # Generic fallback

def strip_edit_tags(filename: str) -> str:
    """
    Removes edit tags from a filename.
    
    Args:
        filename: The filename to process
        
    Returns:
        The filename with edit tags removed
    """
    basename = os.path.basename(filename)
    name, ext = os.path.splitext(basename)
    
    for tag in EDITED_TAGS.keys():
        name = name.replace(tag, "")
    
    # Clean up any double underscores left after tag removal
    name = re.sub(r'_{2,}', '_', name)
    # Remove trailing underscores
    name = name.rstrip('_')
    
    return name + ext

def detect_camera_from_filename(filename: str) -> str:
    """
    Detects the camera model based on filename patterns.
    
    Args:
        filename: The filename to analyze
        
    Returns:
        The detected camera name or "Unknown" if not detected
    """
    basename = os.path.basename(filename)
    name, _ = os.path.splitext(basename)
    
    # Remove edit tags for better matching
    if is_edited(filename):
        name = os.path.splitext(strip_edit_tags(filename))[0]
    
    # Try to match against known patterns
    for pattern, camera in CAMERA_REGEXES.items():
        if re.match(pattern, name):
            logging.debug(f"Camera detected for {filename}: {camera} (pattern: {pattern})")
            return camera
    
    logging.debug(f"No camera pattern match for {filename}")
    return "Unknown"

def detect_media_type(extension: str) -> str:
    """
    Determines the media type based on file extension.
    
    Args:
        extension: The file extension (without the dot)
        
    Returns:
        "Foto", "Video", or "Unknown"
    """
    ext = extension.lower().lstrip('.')
    
    if ext in EXTENSION_TYPES:
        return EXTENSION_TYPES[ext]
    
    logging.warning(f"Unknown file extension: {extension}")
    return "Unknown"

def classify_media_file(filepath: str) -> Tuple[str, str, bool, Optional[str]]:
    """
    Classifies a media file based on its filename and extension.
    
    Args:
        filepath: Path to the media file
        
    Returns:
        Tuple of (media_type, camera, is_edited, edit_type)
    """
    filename = os.path.basename(filepath)
    _, extension = os.path.splitext(filename)
    extension = extension.lstrip('.')
    
    media_type = detect_media_type(extension)
    camera = detect_camera_from_filename(filename)
    edited = is_edited(filename)
    edit_type = get_edit_type(filename) if edited else None
    
    logging.debug(f"Classified {filepath}: type={media_type}, camera={camera}, edited={edited}, edit_type={edit_type}")
    
    return media_type, camera, edited, edit_type
