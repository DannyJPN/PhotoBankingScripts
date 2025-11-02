"""
Module for finding companion files (JPG equivalents, original files for edited versions).

This module implements the logic for pairing media files:
- Alternative formats (RAW, PNG, TIFF) with their JPG equivalents
- Edited files with their original versions
"""

import os
import re
import logging
from typing import Optional, Dict
from pathlib import Path


def find_jpg_equivalent(filename: str, target_folder: str) -> Optional[str]:
    """
    Find JPG equivalent for an alternative format image.

    Searches for a JPG file with the same base name in the target folder structure.

    Args:
        filename: Original filename (e.g., "IMG_1234.PNG")
        target_folder: Base target folder to search in

    Returns:
        Full path to JPG equivalent if found, None otherwise

    Example:
        find_jpg_equivalent("IMG_1234.PNG", "I:/Roztříděno")
        -> "I:/Roztříděno/Foto/JPG/Příroda/2024/10/Canon/IMG_1234.JPG"
    """
    # Extract base name without extension
    base_name = os.path.splitext(filename)[0]

    # Possible JPG extensions
    jpg_extensions = ['.JPG', '.jpg', '.JPEG', '.jpeg']

    # Search in Foto/JPG subdirectory
    foto_jpg_path = os.path.join(target_folder, 'Foto', 'JPG')

    if not os.path.exists(foto_jpg_path):
        logging.debug(f"JPG folder does not exist: {foto_jpg_path}")
        return None

    # Recursively search for JPG with matching base name
    for root, dirs, files in os.walk(foto_jpg_path):
        for file in files:
            file_base_name, file_ext = os.path.splitext(file)

            if file_base_name == base_name and file_ext in jpg_extensions:
                full_path = os.path.join(root, file)
                logging.info(f"Found JPG equivalent for {filename}: {full_path}")
                return full_path

    logging.debug(f"No JPG equivalent found for {filename}")
    return None


def find_original_file(edited_filename: str, target_folder: str, is_video: bool = False) -> Optional[str]:
    """
    Find original file for an edited version.

    Searches for the original (non-edited) version of an edited file.
    For photos: searches JPG first, then same extension.
    For videos: searches any video format.

    Args:
        edited_filename: Edited filename (e.g., "IMG_1234_edited.JPG")
        target_folder: Base target folder to search in
        is_video: True if this is a video file

    Returns:
        Full path to original file if found, None otherwise

    Example:
        find_original_file("IMG_1234_bw.JPG", "I:/Roztříděno", False)
        -> "I:/Roztříděno/Foto/JPG/Příroda/2024/10/Canon/IMG_1234.JPG"
    """
    # Extract base name by removing edit tags
    from sortunsortedmedialib.constants import EDITED_TAGS

    base_name_with_ext = edited_filename
    file_ext = os.path.splitext(edited_filename)[1]

    # Remove edit tags to get original name
    for tag in EDITED_TAGS.keys():
        # Remove tag and preceding underscore
        pattern = f"{tag}(?={re.escape(file_ext)})"
        base_name_with_ext = re.sub(pattern, '', base_name_with_ext, flags=re.IGNORECASE)
        # Also remove underscore before extension if present
        base_name_with_ext = re.sub(r'_+(?=' + re.escape(file_ext) + ')', '', base_name_with_ext)

    original_base_name = os.path.splitext(base_name_with_ext)[0]

    logging.debug(f"Searching for original of {edited_filename}: base name = {original_base_name}")

    # Determine search paths
    if is_video:
        search_root = os.path.join(target_folder, 'Video')
    else:
        # For photos: search JPG first, then same extension
        search_roots = [
            os.path.join(target_folder, 'Foto', 'JPG'),
            os.path.join(target_folder, 'Foto', file_ext.upper().lstrip('.'))
        ]
        search_root = None

    # Search for original file
    if is_video:
        # Video: search in Video folder
        if os.path.exists(search_root):
            for root, dirs, files in os.walk(search_root):
                for file in files:
                    if os.path.splitext(file)[0] == original_base_name:
                        full_path = os.path.join(root, file)
                        logging.info(f"Found original video for {edited_filename}: {full_path}")
                        return full_path
    else:
        # Photo: search JPG first, then same extension
        for search_path in search_roots:
            if not os.path.exists(search_path):
                continue

            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if os.path.splitext(file)[0] == original_base_name:
                        full_path = os.path.join(root, file)
                        logging.info(f"Found original photo for {edited_filename}: {full_path}")
                        return full_path

    logging.debug(f"No original file found for {edited_filename}")
    return None


def extract_metadata_from_path(file_path: str) -> Dict[str, str]:
    """
    Extract metadata (category, camera, date) from file path.

    Parses structured paths like:
    - Foto/JPG/category/year/month/camera/filename.jpg
    - Video/MP4/category/year/month/camera/filename.mp4
    - Upravené Foto/JPG/category/year/month/camera/filename.jpg

    Args:
        file_path: Full path to file

    Returns:
        Dictionary with 'category', 'camera_name', 'year', 'month'

    Example:
        extract_metadata_from_path("I:/Roztříděno/Foto/JPG/Příroda/2024/10/Canon/IMG.JPG")
        -> {'category': 'Příroda', 'camera_name': 'Canon', 'year': '2024', 'month': '10'}
    """
    path_parts = Path(file_path).parts

    # Find the media type index (Foto, Video, or "Upravené Foto"/"Upravené Video")
    media_type_idx = None
    for i, part in enumerate(path_parts):
        if part in ['Foto', 'Video']:
            media_type_idx = i
            break
        elif part == 'Upravené' and i + 1 < len(path_parts) and path_parts[i+1] in ['Foto', 'Video']:
            media_type_idx = i + 1  # Skip "Upravené", use "Foto"/"Video"
            break

    if media_type_idx is None or media_type_idx + 5 >= len(path_parts):
        logging.warning(f"Cannot extract metadata from path: {file_path}")
        return {
            'category': 'Ostatní',
            'camera_name': 'Unknown',
            'year': '',
            'month': ''
        }

    # Structure: .../Foto/Extension/Category/Year/Month/Camera/filename
    extension = path_parts[media_type_idx + 1]  # e.g., "JPG"
    category = path_parts[media_type_idx + 2]    # e.g., "Příroda"
    year = path_parts[media_type_idx + 3]        # e.g., "2024"
    month = path_parts[media_type_idx + 4]       # e.g., "10"
    camera_name = path_parts[media_type_idx + 5] # e.g., "Canon EOS R5"

    logging.debug(f"Extracted metadata from {file_path}: category={category}, camera={camera_name}")

    return {
        'category': category,
        'camera_name': camera_name,
        'year': year,
        'month': month
    }