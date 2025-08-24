import os
import logging
import shutil


def ensure_directory(directory: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory to ensure exists
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logging.debug("Created directory: %s", directory)
    else:
        logging.debug("Directory already exists: %s", directory)


def copy_file(src: str, dest: str, overwrite: bool = True) -> None:
    """
    Copy a file from src to dest using shutil.copy2 for proper metadata preservation.
    
    Args:
        src: Source file path
        dest: Destination file path  
        overwrite: Whether to overwrite existing files
    """
    if not overwrite and os.path.exists(dest):
        logging.debug("File exists and overwrite=False: %s", dest)
        return
    
    try:
        # Ensure destination directory exists
        dest_dir = os.path.dirname(dest)
        if dest_dir:
            ensure_directory(dest_dir)
        
        # Copy file with metadata preservation
        shutil.copy2(src, dest)
        logging.debug("Copied file from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to copy file from %s to %s: %s", src, dest, e)
        raise