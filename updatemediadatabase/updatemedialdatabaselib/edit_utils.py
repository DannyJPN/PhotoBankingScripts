"""
Utilities for handling edited media files.
Contains functions for detecting edit types and modifying metadata.
"""
import os
import re
import logging
from typing import Dict, Optional, Tuple

from updatemedialdatabaselib.regex_definitions import (
    COMPILED_EDIT_PATTERNS,
    ANY_EDIT_PATTERN,
    ORIGINAL_FILENAME_PATTERN
)

def get_edit_type(filename: str) -> Optional[str]:
    """
    Determine the edit type from a filename.
    Returns the edit type name or None if no edit type is detected.
    
    Args:
        filename: The filename to analyze
        
    Returns:
        The edit type name or None if no edit is detected
    """
    filename_lower = filename.lower()
    
    # Check each edit pattern
    for edit_type, pattern in COMPILED_EDIT_PATTERNS.items():
        if pattern.search(filename_lower):
            logging.debug(f"Detected edit type '{edit_type}' in filename: {filename}")
            return edit_type
            
    # No edit type detected
    return None

def is_edited_file(filename: str) -> bool:
    """
    Check if a filename indicates an edited file.
    
    Args:
        filename: The filename to check
        
    Returns:
        True if the file appears to be edited, False otherwise
    """
    return ANY_EDIT_PATTERN.search(filename.lower()) is not None

def get_original_filename(edited_filename: str) -> Optional[str]:
    """
    Extract the original filename from an edited filename.
    
    Args:
        edited_filename: The edited filename
        
    Returns:
        The original filename or None if no match is found
    """
    match = ORIGINAL_FILENAME_PATTERN.match(edited_filename)
    if match:
        original_name = match.group(1) + match.group(2)
        logging.debug(f"Extracted original filename '{original_name}' from '{edited_filename}'")
        return original_name
    return None

def modify_description_for_edit(description: str, edit_type: str) -> str:
    """
    Modify a description to include information about the edit type.
    
    Args:
        description: The original description
        edit_type: The type of edit applied
        
    Returns:
        The modified description
    """
    edit_descriptions = {
        'bw': "Black and white image",
        'sepia': "Sepia-toned image",
        'vintage': "Vintage-style image",
        'blur': "Blurred image",
        'sharpen': "Sharpened image",
        'hdr': "HDR-processed image",
        'panorama': "Panoramic image",
        'crop': "Cropped image",
        'square': "Square crop image",
        'portrait': "Portrait orientation image",
        'landscape': "Landscape orientation image",
        'negative': "Negative image",
        'vignette': "Vignette-applied image",
        'tilt': "Tilt-shift effect image",
        'composite': "Composite image",
        'collage': "Collage image",
        'frame': "Framed image",
        'watermark': "Watermarked image",
        'text': "Text-overlaid image",
        'filter': "Filtered image",
        'effect': "Effect-applied image",
        'art': "Artistic effect image",
        'sketch': "Sketch-style image",
        'cartoon': "Cartoon-style image",
        'oil': "Oil painting effect image",
        'pencil': "Pencil drawing effect image",
        'drawing': "Drawing effect image",
        'painting': "Painting effect image",
        'abstract': "Abstract-style image",
        'grunge': "Grunge-style image",
        'aged': "Aged effect image",
        'color': "Color-enhanced image",
        'enhanced': "Enhanced image",
        'edited': "Edited image",
    }
    
    edit_desc = edit_descriptions.get(edit_type, f"{edit_type.capitalize()} image")
    
    if description and description.strip():
        return f"{edit_desc} - {description}"
    else:
        return edit_desc

def modify_keywords_for_edit(keywords: str, edit_type: str) -> str:
    """
    Add edit-related keywords to the existing keywords.
    
    Args:
        keywords: The original keywords (comma-separated)
        edit_type: The type of edit applied
        
    Returns:
        The modified keywords
    """
    edit_keywords = {
        'bw': ["black and white", "monochrome", "grayscale"],
        'sepia': ["sepia", "brown", "vintage", "retro"],
        'vintage': ["vintage", "retro", "old", "aged"],
        'blur': ["blur", "blurred", "soft focus"],
        'sharpen': ["sharp", "sharpened", "detailed"],
        'hdr': ["hdr", "high dynamic range", "vivid"],
        'panorama': ["panorama", "wide", "panoramic"],
        'crop': ["crop", "cropped", "composition"],
        'square': ["square", "1:1", "instagram"],
        'portrait': ["portrait", "vertical"],
        'landscape': ["landscape", "horizontal"],
        'negative': ["negative", "inverted", "inverse"],
        'vignette': ["vignette", "dark edges", "framed"],
        'tilt': ["tilt-shift", "miniature", "selective focus"],
        'composite': ["composite", "combined", "merged"],
        'collage': ["collage", "collection", "multiple"],
        'frame': ["frame", "border", "framed"],
        'watermark': ["watermark", "copyright", "protected"],
        'text': ["text", "typography", "words"],
        'filter': ["filter", "effect", "processed"],
        'effect': ["effect", "filter", "processed"],
        'art': ["art", "artistic", "creative"],
        'sketch': ["sketch", "drawing", "pencil"],
        'cartoon': ["cartoon", "comic", "animated"],
        'oil': ["oil painting", "painting", "artistic"],
        'pencil': ["pencil", "sketch", "drawing"],
        'drawing': ["drawing", "sketch", "illustration"],
        'painting': ["painting", "artistic", "canvas"],
        'abstract': ["abstract", "non-representational", "artistic"],
        'grunge': ["grunge", "dirty", "textured"],
        'aged': ["aged", "old", "vintage", "retro"],
        'color': ["colorized", "color", "vibrant"],
        'enhanced': ["enhanced", "improved", "processed"],
        'edited': ["edited", "modified", "processed"],
    }
    
    # Get keywords for this edit type
    new_kw = edit_keywords.get(edit_type, [edit_type])
    
    # Split existing keywords
    existing_kw = []
    if keywords and keywords.strip():
        existing_kw = [k.strip().lower() for k in keywords.split(',')]
    
    # Combine keywords, avoiding duplicates
    combined_kw = existing_kw.copy()
    for kw in new_kw:
        if kw.lower() not in [k.lower() for k in combined_kw]:
            combined_kw.append(kw)
    
    # Join keywords with commas
    return ', '.join(combined_kw)

def update_metadata_for_edit(metadata: Dict[str, str], edit_type: str) -> Dict[str, str]:
    """
    Update metadata for an edited file.
    
    Args:
        metadata: The original metadata
        edit_type: The type of edit applied
        
    Returns:
        The updated metadata
    """
    updated = metadata.copy()
    
    # Update description
    if 'Description' in updated:
        updated['Description'] = modify_description_for_edit(updated['Description'], edit_type)
    else:
        updated['Description'] = modify_description_for_edit("", edit_type)
    
    # Update keywords
    if 'Keywords' in updated:
        updated['Keywords'] = modify_keywords_for_edit(updated['Keywords'], edit_type)
    else:
        updated['Keywords'] = ', '.join(edit_keywords.get(edit_type, [edit_type]))
    
    # Add edit type to metadata
    updated['EditType'] = edit_type
    
    return updated
