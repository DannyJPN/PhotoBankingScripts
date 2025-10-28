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
from sortunsortedmedialib.constants import EDITED_TAGS, EXTENSION_TYPES, DEFAULT_MAX_PARALLEL


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
    parent_dir = os.path.dirname(script_dir)  # Go up one level from sortunsortedmedialib/
    sortunsortedmediafile_path = os.path.join(parent_dir, "sortunsortedmediafile.py")
    
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


def process_unmatched_files(unmatched_files: List[str], target_folder: str, interval: int, max_parallel: int = DEFAULT_MAX_PARALLEL) -> None:
    """
    Launch processes for unmatched files in fire-and-forget mode with parallel limit.
    Maintains max_parallel concurrent processes, checking every 'interval' seconds.
    Each process runs independently and can only be closed via its GUI window.
    Main script does not wait for or terminate processes, only monitors them.

    Args:
        unmatched_files: List of unmatched file paths
        target_folder: Target folder for sorted media
        interval: Interval in seconds between process checks and launches
        max_parallel: Maximum number of concurrent processes (default: DEFAULT_MAX_PARALLEL)
    """
    if not unmatched_files:
        logging.info("No unmatched files to process")
        return

    total_files = len(unmatched_files)
    launched_count = 0
    failed_count = 0
    running_processes = []  # List of (process, file_path, file_index) tuples

    print(f"\nLaunching {total_files} processes in fire-and-forget mode...")
    print(f"Max parallel processes: {max_parallel}")
    print(f"Check interval: {interval}s")
    print(f"Each process can be closed individually via its GUI window.")
    print(f"Press Ctrl+C to exit this script (running processes will continue).\n")
    logging.info(f"Starting fire-and-forget processing of {total_files} files (max_parallel={max_parallel}, interval={interval}s)")

    # Get script paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    sortunsortedmediafile_path = os.path.join(parent_dir, "sortunsortedmediafile.py")

    for i, file_path in enumerate(unmatched_files):
        # Clean up finished processes from tracking list
        running_processes = [(p, fp, idx) for p, fp, idx in running_processes if p.poll() is None]

        # Wait until we have a free slot (less than max_parallel running)
        while len(running_processes) >= max_parallel:
            logging.info(f"Waiting for free slot ({len(running_processes)}/{max_parallel} processes running)...")
            print(f"  Waiting for free slot ({len(running_processes)}/{max_parallel} running)...", end='\r')
            time.sleep(interval)
            # Clean up finished processes
            running_processes = [(p, fp, idx) for p, fp, idx in running_processes if p.poll() is None]

        # Now we have a free slot, launch new process
        logging.info(f"Launching process for file {i+1}/{total_files}: {file_path}")
        print(f"\nLaunching {i+1}/{total_files}: {os.path.basename(file_path)}")

        try:
            cmd = [
                sys.executable,
                sortunsortedmediafile_path,
                "--media_file", file_path,
                "--target_folder", target_folder
            ]

            # Launch process in fire-and-forget mode with new console window
            if os.name == 'nt':  # Windows
                # CREATE_NEW_CONSOLE opens new terminal window where Ctrl+C works
                # Start minimized using STARTUPINFO
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 6  # SW_MINIMIZE (6) or SW_SHOWMINNOACTIVE (7)

                process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    startupinfo=startupinfo
                )
            else:  # Unix/Linux
                # Start new session (detached from parent)
                process = subprocess.Popen(
                    cmd,
                    start_new_session=True
                )

            running_processes.append((process, file_path, i+1))
            launched_count += 1
            active_count = len([p for p, _, _ in running_processes if p.poll() is None])
            print(f"  ✓ Launched (PID: {process.pid}) - {active_count}/{max_parallel} slots used")
            logging.info(f"Launched independent process for {file_path} with PID {process.pid}")

        except Exception as e:
            failed_count += 1
            print(f"  ✗ Failed to launch: {str(e)}")
            logging.error(f"Failed to launch process for {file_path}: {e}")

        # Wait interval before launching next process
        if interval > 0 and i < total_files - 1:
            time.sleep(interval)

    # Report launch statistics
    print(f"\n{'='*60}")
    print(f"Launch Summary:")
    print(f"  Total files: {total_files}")
    print(f"  Successfully launched: {launched_count}")
    print(f"  Failed to launch: {failed_count}")
    print(f"  Currently running: {len([p for p, _, _ in running_processes if p.poll() is None])}")
    print(f"\nAll processes launched and running independently.")
    print(f"Close each GUI window to finish processing that file.")
    print(f"Exiting main script now (Ctrl+C or just close).")
    print(f"{'='*60}")

    logging.info(f"Fire-and-forget launch complete. Launched: {launched_count}, Failed: {failed_count}")