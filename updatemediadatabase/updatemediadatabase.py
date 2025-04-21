#!/usr/bin/env python3
"""
UpdateMediaDatabase - Main script

This script analyzes media files (photos and videos), extracts metadata,
and updates a CSV database with the information.

It can detect edited files, link them to their originals, and validate
media against size and resolution limits for different photo banks.
"""
import os
import argparse
import logging
from typing import List, Dict, Any

# Import shared modules
from shared.utils import get_log_filename
from shared.file_operations import ensure_directory, list_files
from shared.logging_config import setup_logging
from shared.csv_operations import load_csv, save_csv

# Import project-specific modules
from updatemedialdatabaselib.constants import (
    DEFAULT_PHOTO_CSV,
    DEFAULT_LIMIT_CSV,
    DEFAULT_PHOTO_DIR,
    DEFAULT_VIDEO_DIR,
    DEFAULT_EDIT_PHOTO_DIR,
    DEFAULT_EDIT_VIDEO_DIR,
    DEFAULT_LOG_DIR,
    DEFAULT_EXIFTOOL_DIR
)
from updatemedialdatabaselib.exif_downloader import ensure_exiftool
from updatemedialdatabaselib.media_processor import process_media_file

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update media database with photo and video metadata."
    )
    parser.add_argument("--photo_csv", type=str, default=DEFAULT_PHOTO_CSV,
                        help="Path to the photo CSV database")
    parser.add_argument("--limit_csv", type=str, default=DEFAULT_LIMIT_CSV,
                        help="Path to the photo limits CSV file")
    parser.add_argument("--photo_dir", type=str, default=DEFAULT_PHOTO_DIR,
                        help="Directory containing original photos")
    parser.add_argument("--video_dir", type=str, default=DEFAULT_VIDEO_DIR,
                        help="Directory containing original videos")
    parser.add_argument("--edit_photo_dir", type=str, default=DEFAULT_EDIT_PHOTO_DIR,
                        help="Directory containing edited photos")
    parser.add_argument("--edit_video_dir", type=str, default=DEFAULT_EDIT_VIDEO_DIR,
                        help="Directory containing edited videos")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--exiftool_dir", type=str, default=DEFAULT_EXIFTOOL_DIR,
                        help="Directory for ExifTool")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    return parser.parse_args()

def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)
    logging.info("Starting UpdateMediaDatabase")
    
    # Ensure ExifTool is available
    try:
        exiftool_path = ensure_exiftool(args.exiftool_dir)
        logging.info(f"Using ExifTool at: {exiftool_path}")
    except Exception as e:
        logging.error(f"Failed to ensure ExifTool: {e}")
        return
    
    # Load existing database
    try:
        database = load_csv(args.photo_csv)
        logging.info(f"Loaded {len(database)} records from database")
    except Exception as e:
        logging.error(f"Failed to load database: {e}")
        database = []
    
    # Load limits
    try:
        limits = load_csv(args.limit_csv)
        logging.info(f"Loaded {len(limits)} photo bank limits")
    except Exception as e:
        logging.error(f"Failed to load limits: {e}")
        limits = []
    
    # Get list of media directories to process
    media_dirs = [
        args.photo_dir,
        args.video_dir,
        args.edit_photo_dir,
        args.edit_video_dir
    ]
    
    # Process each directory
    new_records = []
    for directory in media_dirs:
        if not os.path.exists(directory):
            logging.warning(f"Directory does not exist, skipping: {directory}")
            continue
        
        logging.info(f"Processing directory: {directory}")
        
        # Get all files in the directory
        files = list_files(directory, recursive=True)
        logging.info(f"Found {len(files)} files in {directory}")
        
        # Process each file
        for file_path in files:
            record = process_media_file(file_path, database, limits, exiftool_path)
            if record:
                new_records.append(record)
    
    # Update database with new records
    if new_records:
        logging.info(f"Adding {len(new_records)} new records to database")
        updated_database = database + new_records
        
        # Save updated database
        try:
            save_csv(args.photo_csv, updated_database, backup=True)
            logging.info(f"Saved updated database with {len(updated_database)} records")
        except Exception as e:
            logging.error(f"Failed to save database: {e}")
    else:
        logging.info("No new records to add to database")
    
    logging.info("UpdateMediaDatabase completed successfully")

if __name__ == "__main__":
    main()
