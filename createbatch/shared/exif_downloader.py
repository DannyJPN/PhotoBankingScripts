import os
import logging
from createbatchlib.constants import EXIFTOOL_PATH

def ensure_exiftool(tool_dir: str = None) -> str:
    """
    Returns the path to ExifTool executable from constants.
    
    Args:
        tool_dir: Ignored - path is fixed in constants
        
    Returns:
        Path to the ExifTool executable
    """
    if os.path.exists(EXIFTOOL_PATH):
        logging.info(f"ExifTool found at {EXIFTOOL_PATH}")
        return EXIFTOOL_PATH
    else:
        logging.error(f"ExifTool not found at configured path: {EXIFTOOL_PATH}")
        raise FileNotFoundError(f"ExifTool not found at {EXIFTOOL_PATH}")