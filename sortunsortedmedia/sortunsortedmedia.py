#!/usr/bin/env python3
"""
Main script for processing and sorting unsorted media files.
"""

import os
import sys
import time
import argparse
import logging
import subprocess
from typing import List, Dict

from shared.utils import get_log_filename
from shared.file_operations import ensure_directory, list_files
from shared.logging_config import setup_logging

from sortunsortedmedialib.constants import DEFAULT_UNSORTED_FOLDER, DEFAULT_TARGET_FOLDER, DEFAULT_INTERVAL
from sortunsortedmedialib.matching_engine import find_unmatched_media
from sortunsortedmedialib.interactive import open_media_file, confirm_action

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process and sort unsorted media files."
    )
    parser.add_argument("--unsorted_folder", type=str, default=DEFAULT_UNSORTED_FOLDER,
                        help="Folder containing unsorted media files")
    parser.add_argument("--target_folder", type=str, default=DEFAULT_TARGET_FOLDER,
                        help="Target folder for sorted media")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help="Interval in seconds to wait between processing files")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    return parser.parse_args()

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

def process_unmatched_files(unmatched_files: List[str], target_folder: str, interval: int) -> None:
    """
    Process unmatched files by opening them and calling sortunsortedmediafile.py.

    Args:
        unmatched_files: List of unmatched file paths
        target_folder: Target folder for sorted media
        interval: Interval in seconds to wait between processing files
    """
    if not unmatched_files:
        logging.info("No unmatched files to process")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    sortunsortedmediafile_path = os.path.join(script_dir, "sortunsortedmediafile.py")

    for i, file_path in enumerate(unmatched_files):
        logging.info(f"Processing file {i+1}/{len(unmatched_files)}: {file_path}")
        print(f"\nProcessing file {i+1}/{len(unmatched_files)}:")
        print(f"  {os.path.basename(file_path)}")

        # Open the file in an appropriate editor
        open_appropriate_editor(file_path)

        # Run sortunsortedmediafile.py
        try:
            cmd = [
                sys.executable,
                sortunsortedmediafile_path,
                "--media_file", file_path,
                "--target_folder", target_folder
            ]

            subprocess.run(cmd, check=True)
            logging.info(f"Successfully processed {file_path}")

            # Wait for the specified interval
            if i < len(unmatched_files) - 1 and interval > 0:
                print(f"\nWaiting {interval} seconds before next file...")
                time.sleep(interval)

        except subprocess.CalledProcessError as e:
            logging.error(f"Error processing {file_path}: {e}")
            if not confirm_action("Continue with next file?"):
                logging.info("User chose to stop processing")
                break

def main():
    """Main function."""
    args = parse_arguments()

    # Setup logging
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    ensure_directory(log_dir)
    log_file = get_log_filename(log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    logging.info("Starting unsorted media processing")
    logging.info(f"Unsorted folder: {args.unsorted_folder}")
    logging.info(f"Target folder: {args.target_folder}")

    # Find unmatched media files
    unmatched = find_unmatched_media(args.unsorted_folder, args.target_folder)

    # Process each type of unmatched files
    for file_type, files in unmatched.items():
        if not files:
            continue

        logging.info(f"Processing {len(files)} unmatched {file_type} files")
        print(f"\n=== Processing {len(files)} unmatched {file_type} files ===")

        if confirm_action(f"Process {len(files)} {file_type} files?"):
            process_unmatched_files(files, args.target_folder, args.interval)
        else:
            logging.info(f"Skipping {file_type} files as per user request")

    logging.info("Unsorted media processing completed")
    print("\nAll media processing completed!")

if __name__ == "__main__":
    main()
