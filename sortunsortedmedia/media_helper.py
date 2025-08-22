"""
Helper functions for media file processing.
"""

import os
import sys
import time
import logging
import subprocess
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from shared.file_operations import list_files
from sortunsortedmedialib.constants import EDITED_TAGS, EXTENSION_TYPES


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


def confirm_action(prompt: str, default: bool = True) -> bool:
    """Asks the user to confirm an action."""
    default_text = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_text}]: ").strip().lower()
    
    if not response:
        return default
    
    return response.startswith('y')


def is_media_file(file_path: str) -> bool:
    """Check if file is a multimedia file based on extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower().lstrip('.')
    return ext in EXTENSION_TYPES


def is_edited_file(filename: str) -> bool:
    """Check if file has edited tags based on constants."""
    basename = os.path.basename(filename)
    name, _ = os.path.splitext(basename)
    
    for tag in EDITED_TAGS.keys():
        if tag.lower() in name.lower():
            return True
    return False


def is_video_file(file_path: str) -> bool:
    """Check if file is a video based on extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower().lstrip('.')
    return ext in EXTENSION_TYPES and EXTENSION_TYPES[ext] == "Video"


def is_jpg_file(file_path: str) -> bool:
    """Check if file is JPG/JPEG."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    return ext in ['.jpg', '.jpeg']


def find_unmatched_media(unsorted_folder: str, target_folder: str) -> Dict[str, List[str]]:
    """
    Finds media files in the unsorted folder that don't exist in the target folder.
    Returns categorized dictionary with proper ordering:
    1. jpg_files - JPG/JPEG files (unedited)
    2. other_images - Other image files (unedited)  
    3. videos - Video files (unedited)
    4. edited_images - Image files with edited tags
    5. edited_videos - Video files with edited tags
    
    Args:
        unsorted_folder: Path to the folder with unsorted media
        target_folder: Path to the target folder
        
    Returns:
        Dictionary with categorized lists of unmatched file paths
    """
    # List all files in both folders
    unsorted_files = list_files(unsorted_folder, recursive=True)
    target_files = list_files(target_folder, recursive=True)
    
    # Extract basenames from target files for faster matching
    target_basenames = set()
    for target_path in target_files:
        target_basenames.add(os.path.basename(target_path).lower())
    
    # Initialize categories
    jpg_files = []
    other_images = []
    videos = []
    edited_images = []
    edited_videos = []
    
    for file_path in unsorted_files:
        # Only process multimedia files
        if not is_media_file(file_path):
            continue
            
        filename = os.path.basename(file_path)
        
        # Check if file exists in target folder
        if filename.lower() not in target_basenames:
            is_edited = is_edited_file(filename)
            is_video = is_video_file(file_path)
            is_jpg = is_jpg_file(file_path)
            
            if is_edited:
                if is_video:
                    edited_videos.append(file_path)
                else:
                    edited_images.append(file_path)
            else:
                if is_jpg:
                    jpg_files.append(file_path)
                elif is_video:
                    videos.append(file_path)
                else:
                    other_images.append(file_path)
    
    result = {
        'jpg_files': jpg_files,
        'other_images': other_images,
        'videos': videos,
        'edited_images': edited_images,
        'edited_videos': edited_videos
    }
    
    total_files = sum(len(files) for files in result.values())
    logging.info(f"Found {total_files} unmatched media files: "
                f"JPG: {len(jpg_files)}, Other images: {len(other_images)}, "
                f"Videos: {len(videos)}, Edited images: {len(edited_images)}, "
                f"Edited videos: {len(edited_videos)}")
    
    return result


def open_appropriate_editor(file_path: str) -> bool:
    """
    Opens the appropriate editor for the given file type.

    Args:
        file_path: Path to the file to open

    Returns:
        True if an editor was opened, False otherwise
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # Photo editors
    photo_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.raw', '.arw', '.cr2', '.nef']
    # Video extensions
    video_extensions = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.webm']

    try:
        if ext in photo_extensions:
            # Try to open with Photoshop if available, otherwise use system default
            if os.name == 'nt':  # Windows
                photoshop_paths = [
                    r"C:\Program Files\Adobe\Adobe Photoshop 2023\Photoshop.exe",
                    r"C:\Program Files\Adobe\Adobe Photoshop 2022\Photoshop.exe",
                    r"C:\Program Files\Adobe\Adobe Photoshop 2021\Photoshop.exe",
                    r"C:\Program Files\Adobe\Adobe Photoshop CC 2020\Photoshop.exe",
                    r"C:\Program Files\Adobe\Adobe Photoshop CC 2019\Photoshop.exe"
                ]

                for ps_path in photoshop_paths:
                    if os.path.exists(ps_path):
                        subprocess.Popen([ps_path, file_path])
                        logging.info(f"Opened {file_path} with Photoshop")
                        return True

            # Fallback to system default
            return open_media_file(file_path)

        elif ext in video_extensions:
            # Try to open with VLC if available, otherwise use system default
            if os.name == 'nt':  # Windows
                vlc_paths = [
                    r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                    r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
                ]

                for vlc_path in vlc_paths:
                    if os.path.exists(vlc_path):
                        subprocess.Popen([vlc_path, file_path])
                        logging.info(f"Opened {file_path} with VLC")
                        return True

            # Fallback to system default
            return open_media_file(file_path)

        else:
            # Use system default for other file types
            return open_media_file(file_path)

    except Exception as e:
        logging.error(f"Error opening editor for {file_path}: {e}")
        return False


def process_single_file(file_path: str, target_folder: str, file_index: int, total_files: int) -> tuple:
    """
    Process a single file using subprocess.
    
    Args:
        file_path: Path to the file to process
        target_folder: Target folder for sorted media
        file_index: Current file index (1-based)
        total_files: Total number of files
        
    Returns:
        Tuple of (success: bool, file_path: str, error: str or None)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sortunsortedmediafile_path = os.path.join(script_dir, "sortunsortedmediafile.py")
    
    logging.info(f"Processing file {file_index}/{total_files}: {file_path}")
    print(f"\nProcessing file {file_index}/{total_files}: {os.path.basename(file_path)}")
    
    try:
        cmd = [
            sys.executable,
            sortunsortedmediafile_path,
            "--media_file", file_path,
            "--target_folder", target_folder
        ]
        
        subprocess.run(cmd, check=True)
        logging.info(f"Successfully processed {file_path}")
        return True, file_path, None
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Process returned non-zero exit status: {e.returncode}"
        logging.error(f"Error processing {file_path}: {error_msg}")
        return False, file_path, error_msg
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error processing {file_path}: {error_msg}")
        return False, file_path, error_msg


def process_unmatched_files(unmatched_files: List[str], target_folder: str, interval: int, max_parallel: int = 3) -> None:
    """
    Process unmatched files in parallel using multiple threads.
    Each file opens its own window without waiting for previous ones to close.

    Args:
        unmatched_files: List of unmatched file paths
        target_folder: Target folder for sorted media
        interval: Interval in seconds to wait between launching new processes
        max_parallel: Maximum number of parallel processes (default: 3)
    """
    if not unmatched_files:
        logging.info("No unmatched files to process")
        return

    total_files = len(unmatched_files)
    completed_count = 0
    failed_files = []
    
    print(f"\nStarting parallel processing of {total_files} files...")
    logging.info(f"Starting parallel processing with max {max_parallel} parallel processes")

    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        # Submit all tasks
        future_to_file = {}
        for i, file_path in enumerate(unmatched_files):
            future = executor.submit(process_single_file, file_path, target_folder, i+1, total_files)
            future_to_file[future] = file_path
            
            # Add interval between launching processes to avoid overwhelming the system
            if interval > 0 and i < total_files - 1:
                time.sleep(interval)
        
        # Process completed tasks as they finish
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            completed_count += 1
            
            try:
                success, processed_file, error = future.result()
                if success:
                    print(f"✓ Completed {completed_count}/{total_files}: {os.path.basename(processed_file)}")
                else:
                    failed_files.append((processed_file, error))
                    print(f"✗ Failed {completed_count}/{total_files}: {os.path.basename(processed_file)} - {error}")
                    
            except Exception as e:
                failed_files.append((file_path, str(e)))
                print(f"✗ Failed {completed_count}/{total_files}: {os.path.basename(file_path)} - {str(e)}")
    
    # Report final statistics
    successful_count = total_files - len(failed_files)
    print(f"\n=== Processing Complete ===")
    print(f"Total files: {total_files}")
    print(f"Successfully processed: {successful_count}")
    print(f"Failed: {len(failed_files)}")
    
    logging.info(f"Processing complete. Success: {successful_count}, Failed: {len(failed_files)}")
    
    if failed_files:
        print(f"\nFailed files:")
        for file_path, error in failed_files:
            print(f"  - {os.path.basename(file_path)}: {error}")
            logging.error(f"Failed to process {file_path}: {error}")