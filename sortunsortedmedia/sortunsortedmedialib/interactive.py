"""
Interactive module for getting user input for media categorization.
"""

import os
import logging
import subprocess
import platform
from typing import Optional, List

from sortunsortedmedialib.constants import DEFAULT_CATEGORIES

def open_media_file(media_path: str) -> bool:
    """
    Opens a media file with the default system application.
    
    Args:
        media_path: Path to the media file
        
    Returns:
        True if the file was opened successfully, False otherwise
    """
    if not os.path.exists(media_path):
        logging.error(f"File not found: {media_path}")
        return False
    
    try:
        system = platform.system()
        
        if system == "Windows":
            os.startfile(media_path)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", media_path], check=True)
        else:  # Linux and other Unix-like
            subprocess.run(["xdg-open", media_path], check=True)
            
        logging.info(f"Opened file: {media_path}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to open file {media_path}: {e}")
        return False

def ask_for_category(media_path: str, categories: List[str] = None) -> str:
    """
    Asks the user to select a category for the media file.
    Opens the file for preview before asking.
    
    Args:
        media_path: Path to the media file
        categories: List of available categories. If None, uses DEFAULT_CATEGORIES
        
    Returns:
        The selected category
    """
    if categories is None:
        categories = DEFAULT_CATEGORIES
    
    # Open the file for preview
    open_media_file(media_path)
    
    # Print the filename
    filename = os.path.basename(media_path)
    print(f"\nCategorizing: {filename}")
    
    # Display available categories
    print("\nAvailable categories:")
    for i, category in enumerate(categories, 1):
        print(f"{i}. {category}")
    
    # Ask for input
    while True:
        try:
            choice = input("\nSelect category number (or type a custom category): ")
            
            # Check if input is a number
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(categories):
                    selected = categories[index]
                    logging.info(f"Selected category for {filename}: {selected}")
                    return selected
                else:
                    print(f"Please enter a number between 1 and {len(categories)}")
            else:
                # Custom category
                if choice.strip():
                    logging.info(f"Custom category for {filename}: {choice}")
                    return choice.strip()
                else:
                    print("Please enter a valid category name")
                    
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return "Ostatní"  # Default to "Other" if cancelled
        except Exception as e:
            logging.error(f"Error getting category input: {e}")
            print("An error occurred. Please try again.")

def confirm_action(prompt: str, default: bool = True) -> bool:
    """
    Asks the user to confirm an action.
    
    Args:
        prompt: The prompt to display
        default: The default action if the user just presses Enter
        
    Returns:
        True if confirmed, False otherwise
    """
    default_text = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_text}]: ").strip().lower()
    
    if not response:
        return default
    
    return response.startswith('y')
