"""
Module for downloading and ensuring ExifTool is available.
"""
import os
import sys
import logging
import zipfile
import shutil
import subprocess
from urllib.request import urlretrieve
from typing import Optional

def ensure_exiftool(exiftool_dir: str) -> str:
    """
    Ensure that ExifTool is available in the specified directory.
    If not, download and extract it.
    
    Args:
        exiftool_dir: Directory where ExifTool should be located
        
    Returns:
        Path to the ExifTool executable
    """
    # Create directory if it doesn't exist
    os.makedirs(exiftool_dir, exist_ok=True)
    
    # Check if ExifTool is already available
    exiftool_exe = os.path.join(exiftool_dir, "exiftool.exe")
    if os.path.exists(exiftool_exe):
        logging.info(f"ExifTool found at: {exiftool_exe}")
        return exiftool_exe
    
    # Download ExifTool
    logging.info("ExifTool not found. Downloading...")
    exiftool_zip = os.path.join(exiftool_dir, "exiftool.zip")
    exiftool_url = "https://exiftool.org/exiftool-12.60.zip"  # Use a specific version for stability
    
    try:
        # Download the zip file
        urlretrieve(exiftool_url, exiftool_zip)
        logging.info(f"Downloaded ExifTool to: {exiftool_zip}")
        
        # Extract the zip file
        with zipfile.ZipFile(exiftool_zip, 'r') as zip_ref:
            zip_ref.extractall(exiftool_dir)
        logging.info(f"Extracted ExifTool to: {exiftool_dir}")
        
        # Find the extracted directory (it usually has a version number)
        extracted_dirs = [d for d in os.listdir(exiftool_dir) if os.path.isdir(os.path.join(exiftool_dir, d)) and d.startswith("exiftool")]
        if not extracted_dirs:
            raise FileNotFoundError("Could not find extracted ExifTool directory")
        
        extracted_dir = os.path.join(exiftool_dir, extracted_dirs[0])
        
        # Find the executable
        extracted_exe = os.path.join(extracted_dir, "exiftool(-k).exe")
        if not os.path.exists(extracted_exe):
            raise FileNotFoundError(f"Could not find ExifTool executable in {extracted_dir}")
        
        # Rename and move the executable
        shutil.copy2(extracted_exe, exiftool_exe)
        logging.info(f"Installed ExifTool to: {exiftool_exe}")
        
        # Clean up
        os.remove(exiftool_zip)
        shutil.rmtree(extracted_dir)
        logging.info("Cleaned up temporary files")
        
        return exiftool_exe
    except Exception as e:
        logging.error(f"Failed to download and install ExifTool: {e}")
        raise
