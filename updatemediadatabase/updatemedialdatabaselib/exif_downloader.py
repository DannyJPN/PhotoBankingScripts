"""
Module for ensuring ExifTool is available.
Unified implementation compatible with other scripts.
"""
import os
import logging
from updatemedialdatabaselib.constants import EXIFTOOL_PATH

def ensure_exiftool(tool_dir: str = None) -> str:
    """
    Returns the path to ExifTool executable from constants.
    Compatible with other scripts (sortunsortedmedia, createbatch, givephotobankreadymediafiles).
    
    Args:
        tool_dir: Ignored - kept for compatibility
        
    Returns:
        Path to the ExifTool executable
    """
    if os.path.exists(EXIFTOOL_PATH):
        logging.debug(f"ExifTool found at {EXIFTOOL_PATH}")
        return EXIFTOOL_PATH
    else:
        logging.error(f"ExifTool not found at configured path: {EXIFTOOL_PATH}")
        raise FileNotFoundError(f"ExifTool not found at {EXIFTOOL_PATH}")