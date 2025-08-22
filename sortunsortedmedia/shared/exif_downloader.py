import os
import logging
import requests
import zipfile
import platform
import shutil
from pathlib import Path

def ensure_exiftool() -> str:
    """
    Returns the path to the ExifTool executable.
    Uses the hardcoded path to the existing ExifTool installation.
    
    Returns:
        Path to the ExifTool executable
        
    Raises:
        FileNotFoundError: If ExifTool is not found at the expected location
    """
    # Hardcoded path to ExifTool 12.30
    exiftool_path = r"F:\Dropbox\exiftool-12.30\exiftool.exe"
    
    # Check if ExifTool exists at the expected location
    if os.path.exists(exiftool_path) and os.access(exiftool_path, os.X_OK):
        logging.info(f"ExifTool found at {exiftool_path}")
        return exiftool_path
    
    # ExifTool not found at expected location
    logging.error(f"ExifTool not found at expected location: {exiftool_path}")
    logging.error("Please ensure ExifTool 12.30 is installed at F:\\Dropbox\\exiftool-12.30\\exiftool.exe")
    raise FileNotFoundError(f"ExifTool not found at {exiftool_path}")
