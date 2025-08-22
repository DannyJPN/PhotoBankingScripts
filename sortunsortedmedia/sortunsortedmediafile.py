#!/usr/bin/env python3
"""
Script for processing and sorting a single media file.
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime
from typing import Optional

from shared.utils import get_log_filename
from shared.file_operations import ensure_directory, move_file
from shared.logging_config import setup_logging
from shared.exif_handler import get_best_creation_date

from sortunsortedmedialib.constants import DEFAULT_TARGET_FOLDER
from sortunsortedmedialib.media_classifier import classify_media_file
from sortunsortedmedialib.interactive import ask_for_category
from sortunsortedmedialib.path_builder import build_target_path, ensure_unique_path

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process and sort a single media file."
    )
    parser.add_argument("--media_file", type=str, required=True,
                        help="Path to the media file to process")
    parser.add_argument("--target_folder", type=str, default=DEFAULT_TARGET_FOLDER,
                        help="Target folder for sorted media")
    parser.add_argument("--interval", type=int, default=60,
                        help="Interval in seconds to wait after processing")
    parser.add_argument("--log_file", type=str, default=None,
                        help="Path to log file (default: auto-generated)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    return parser.parse_args()

def process_media_file(media_path: str, target_folder: str) -> Optional[str]:
    """
    Process a single media file and move it to the appropriate location.

    Args:
        media_path: Path to the media file
        target_folder: Base target folder

    Returns:
        The path where the file was moved, or None if processing failed
    """
    if not os.path.exists(media_path):
        logging.error(f"Media file not found: {media_path}")
        return None

    try:
        # Get file information
        filename = os.path.basename(media_path)
        _, extension = os.path.splitext(filename)
        extension = extension.lstrip('.')

        # Classify the media file
        media_type, camera, is_edited, edit_type = classify_media_file(media_path)

        if media_type == "Unknown":
            logging.warning(f"Unknown media type for file: {media_path}")
            return None

        # Get the creation date
        creation_date = get_best_creation_date(media_path)
        if creation_date is None:
            logging.warning(f"Could not determine creation date for {media_path}, using current time")
            creation_date = datetime.now()

        # Show GUI to get category and camera from user
        from media_viewer import show_media_viewer
        
        # Variables to store user selection
        selected_category = None
        selected_camera = None
        
        def completion_callback(category: str, camera: str):
            nonlocal selected_category, selected_camera
            selected_category = category
            selected_camera = camera
        
        # Show GUI
        show_media_viewer(media_path, target_folder, completion_callback)
        
        # Use the selected values or defaults
        category = selected_category if selected_category else "Ostatní"
        if selected_camera and selected_camera != "Unknown":
            camera = selected_camera

        # Build target directory path
        target_dir = build_target_path(
            base_folder=target_folder,
            media_type=media_type,
            extension=extension,
            category=category,
            date=creation_date,
            camera_name=camera,
            is_edited=is_edited,
            edit_type=edit_type
        )
        
        # Full target path with filename
        target_path = os.path.join(target_dir, filename)

        # Ensure the target path is unique
        unique_target_path = ensure_unique_path(target_path)

        # Ensure target directory exists
        target_dir = os.path.dirname(unique_target_path)
        ensure_directory(target_dir)

        # Move the file
        move_file(media_path, unique_target_path)
        logging.info(f"Moved {media_path} to {unique_target_path}")

        return unique_target_path

    except Exception as e:
        logging.error(f"Error processing media file {media_path}: {e}", exc_info=True)
        return None

def main():
    """Main function."""
    args = parse_arguments()

    # Setup logging
    log_file = args.log_file
    if log_file is None:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        ensure_directory(log_dir)
        log_file = get_log_filename(log_dir)

    setup_logging(debug=args.debug, log_file=log_file)
    logging.info(f"Starting media file processing: {args.media_file}")

    # Process the media file
    result_path = process_media_file(args.media_file, args.target_folder)

    if result_path:
        logging.info(f"Successfully processed media file to: {result_path}")
        print(f"\nFile moved to: {result_path}")
    else:
        logging.error(f"Failed to process media file: {args.media_file}")
        print("\nFailed to process media file.")

    # Wait for the specified interval
    if args.interval > 0:
        logging.info(f"Waiting for {args.interval} seconds...")
        time.sleep(args.interval)

    logging.info("Media file processing completed")

if __name__ == "__main__":
    main()
