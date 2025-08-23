"""
Media classifier module for detecting media origins, edits, and extensions.
"""

import os
import re
import logging
from sortunsortedmedialib.media_helper import is_video_file, is_edited_file
from sortunsortedmedialib.constants import CAMERA_REGEXES
from sortunsortedmedialib.exif_camera_detector import combine_regex_and_exif_detection


def classify_media_file(file_path: str) -> tuple[str, str, bool, str]:
    """
    Classify a media file and return its properties.
    
    Args:
        file_path: Path to the media file
        
    Returns:
        Tuple of (media_type, camera, is_edited, edit_type)
    """
    filename = os.path.basename(file_path)
    name, _ = os.path.splitext(filename)
    
    # Determine media type
    _, ext = os.path.splitext(file_path)
    ext = ext.lower().lstrip('.')
    
    from sortunsortedmedialib.constants import EXTENSION_TYPES
    media_type = EXTENSION_TYPES.get(ext, "Foto")
    
    # Check if edited
    is_edited = is_edited_file(filename)
    edit_type = "Unknown" if is_edited else ""
    
    # Camera detection using regex patterns
    regex_camera = detect_camera_from_filename(name)
    
    # Combine regex and EXIF detection
    camera = combine_regex_and_exif_detection(file_path, regex_camera)
    
    return media_type, camera, is_edited, edit_type


def detect_camera_from_filename(filename: str) -> str:
    """
    Detect camera from filename using regex patterns.
    
    Args:
        filename: Base filename without extension
        
    Returns:
        Camera name or "Unknown"
    """
    for pattern, camera in CAMERA_REGEXES.items():
        if re.match(pattern, filename):
            logging.debug(f"Regex matched '{pattern}' -> '{camera}' for filename '{filename}'")
            return camera
    
    logging.debug(f"No regex pattern matched for filename '{filename}'")
    return "Unknown"
