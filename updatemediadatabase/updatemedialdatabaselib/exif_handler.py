"""
Module for handling EXIF metadata operations using ExifTool.
"""
import os
import subprocess
import logging
from typing import Dict, Optional, List

def update_exif_metadata(file_path: str, metadata: Dict[str, str], exiftool_path: str) -> bool:
    """
    Update EXIF metadata for a file using ExifTool.
    
    Args:
        file_path: Path to the file to update
        metadata: Dictionary of metadata tags and values to update
        exiftool_path: Path to the ExifTool executable
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return False
        
    if not os.path.exists(exiftool_path):
        logging.error(f"ExifTool not found: {exiftool_path}")
        return False
    
    # Build ExifTool command
    command = [exiftool_path, "-overwrite_original"]
    
    # Add metadata tags
    for tag, value in metadata.items():
        if value:  # Only add non-empty values
            command.append(f"-{tag}={value}")
    
    # Add file path
    command.append(file_path)
    
    try:
        # Run ExifTool
        logging.debug(f"Running ExifTool command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Check for success
        if "1 image files updated" in result.stdout:
            logging.debug(f"Successfully updated metadata for: {file_path}")
            return True
        else:
            logging.warning(f"ExifTool did not report updating the file: {file_path}")
            logging.debug(f"ExifTool output: {result.stdout}")
            return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to update metadata for {file_path}: {e}")
        logging.debug(f"ExifTool stderr: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Error updating metadata for {file_path}: {e}")
        return False
