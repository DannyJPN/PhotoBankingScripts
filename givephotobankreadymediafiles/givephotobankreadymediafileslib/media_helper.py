"""
Helper functions for media file processing - simplified for givephotobankreadymediafiles.
"""

import os
import sys
import logging
import subprocess
from typing import List, Dict, Tuple
from givephotobankreadymediafileslib.constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS


def open_media_file(media_path: str) -> bool:
    """Opens a media file with the default system application."""
    if not os.path.exists(media_path):
        logging.error(f"File not found: {media_path}")
        return False
    
    try:
        if os.name == 'nt':  # Windows
            os.startfile(media_path)
        else:
            subprocess.run(["xdg-open", media_path], check=True)
        logging.info(f"Opened file: {media_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to open file {media_path}: {e}")
        return False


def is_media_file(file_path: str) -> bool:
    """Check if file is a multimedia file based on extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    return ext in IMAGE_EXTENSIONS or ext in VIDEO_EXTENSIONS


def is_video_file(file_path: str) -> bool:
    """Check if file is a video based on extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    return ext in VIDEO_EXTENSIONS


def is_image_file(file_path: str) -> bool:
    """Check if file is an image based on extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    return ext in IMAGE_EXTENSIONS


def is_jpg_file(file_path: str) -> bool:
    """Check if file is JPG/JPEG."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    return ext in ['.jpg', '.jpeg']


def get_file_info(file_path: str) -> Dict[str, any]:
    """Get basic file information."""
    if not os.path.exists(file_path):
        return {}
    
    stat_info = os.stat(file_path)
    
    return {
        'path': file_path,
        'name': os.path.basename(file_path),
        'size': stat_info.st_size,
        'modified': stat_info.st_mtime,
        'media_type': get_media_type(file_path),
        'extension': os.path.splitext(file_path)[1].lower()
    }


def get_media_type(file_path: str) -> str:
    """Get media type string for file."""
    if is_image_file(file_path):
        return "image"
    elif is_video_file(file_path):
        return "video"
    else:
        return "unknown"


def process_single_file(file_path: str) -> Tuple[bool, str, str]:
    """
    Process a single file using subprocess.
    
    Args:
        file_path: Path to the media file
        
    Returns:
        Tuple of (success, file_path, error_message)
    """
    logging.info(f"Processing {file_path}")
    
    if not os.path.exists(file_path):
        error_msg = "File not found"
        logging.error(f"File not found: {file_path}")
        return False, file_path, error_msg
    
    # Get the preparemediafile.py script path
    script_dir = os.path.dirname(os.path.dirname(__file__))
    preparemediafile_path = os.path.join(script_dir, "preparemediafile.py")
    
    if not os.path.exists(preparemediafile_path):
        error_msg = f"preparemediafile.py not found at {preparemediafile_path}"
        logging.error(error_msg)
        return False, file_path, error_msg
    
    try:
        cmd = [
            sys.executable,
            preparemediafile_path,
            file_path
        ]
        
        subprocess.run(cmd, check=True)
        logging.info(f"Successfully processed {file_path}")
        return True, file_path, ""
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Process returned non-zero exit status: {e.returncode}"
        logging.error(f"Error processing {file_path}: {error_msg}")
        return False, file_path, error_msg
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error processing {file_path}: {error_msg}")
        return False, file_path, error_msg


def process_unmatched_files(records: List[Dict[str, str]], config=None, max_count: int = 1) -> Dict[str, int]:
    """
    Process media records sequentially, like PowerShell version.
    
    Args:
        records: List of unprocessed records
        config: Global configuration object (passed to GUI if needed)
        max_count: Maximum number of files to process (default: 1)
        
    Returns:
        Dictionary with processing statistics
    """
    from givephotobankreadymediafileslib.constants import COL_PATH, COL_FILE
    
    logging.info(f"Processing {min(len(records), max_count)} files sequentially")
    
    stats = {
        'processed': 0,
        'failed': 0,
        'skipped': 0
    }
    
    # Process up to max_count files
    for i in range(min(len(records), max_count)):
        record = records[i]
        file_path = record.get(COL_PATH, "")
        file_name = record.get(COL_FILE, "Unknown")
        
        print(f"Processing [{i+1}/{min(len(records), max_count)}]: {file_name}")
        
        if not file_path:
            logging.warning(f"No file path for record: {file_name}")
            stats['skipped'] += 1
            continue
        
        # Process the file
        success, processed_file, error_msg = process_single_file(file_path)
        
        if success:
            stats['processed'] += 1
            logging.info(f"Prepared file {file_path}")
        else:
            stats['failed'] += 1
            logging.error(f"Failed to prepare file {file_path}: {error_msg}")
            # Continue with next file even if one fails
    
    logging.info(f"Sequential processing complete: {stats}")
    return stats