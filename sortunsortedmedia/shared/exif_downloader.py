import os
import logging
import requests
import zipfile
import platform
import shutil
from pathlib import Path

def ensure_exiftool(tool_dir: str = None) -> str:
    """
    Ensures that ExifTool is available for use.
    
    Args:
        tool_dir: Directory where ExifTool should be stored. If None, uses a default location.
        
    Returns:
        Path to the ExifTool executable
    """
    if tool_dir is None:
        # Use a default location in the user's home directory
        tool_dir = os.path.join(os.path.expanduser("~"), ".exiftool")
    
    os.makedirs(tool_dir, exist_ok=True)
    
    # Determine the platform and set the appropriate ExifTool executable path
    is_windows = platform.system() == "Windows"
    exiftool_exe = "exiftool.exe" if is_windows else "exiftool"
    exiftool_path = os.path.join(tool_dir, exiftool_exe)
    
    # Check if ExifTool is already available
    if os.path.exists(exiftool_path) and os.access(exiftool_path, os.X_OK):
        logging.info(f"ExifTool found at {exiftool_path}")
        return exiftool_path
    
    # ExifTool not found, need to download it
    logging.info("ExifTool not found. Downloading...")
    
    if is_windows:
        # Download Windows version
        url = "https://exiftool.org/exiftool-12.70.zip"
        zip_path = os.path.join(tool_dir, "exiftool.zip")
        
        try:
            # Download the zip file
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tool_dir)
            
            # Rename the extracted executable
            extracted_exe = os.path.join(tool_dir, "exiftool(-k).exe")
            if os.path.exists(extracted_exe):
                shutil.move(extracted_exe, exiftool_path)
            
            # Clean up
            os.remove(zip_path)
            
            logging.info(f"ExifTool downloaded and installed at {exiftool_path}")
            return exiftool_path
            
        except Exception as e:
            logging.error(f"Failed to download and install ExifTool: {e}")
            raise
    else:
        # For non-Windows platforms, suggest using package manager
        logging.error("ExifTool not found. On Linux/Mac, please install ExifTool using your package manager.")
        logging.error("For example: 'sudo apt-get install exiftool' on Ubuntu or 'brew install exiftool' on macOS")
        raise FileNotFoundError("ExifTool not found and automatic installation is only supported on Windows")
