"""
Interactive module for getting user input for media categorization.
"""

import logging


def ask_for_category(media_path: str) -> str:
    """
    Ask user for category for a media file.
    For now returns a default category since we use GUI.
    
    Args:
        media_path: Path to the media file
        
    Returns:
        Category name
    """
    logging.info(f"Interactive category request for: {media_path}")
    return "Ostatní"  # Default category

