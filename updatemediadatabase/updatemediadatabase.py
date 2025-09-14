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
from tqdm import tqdm

# Import project-specific modules
from updatemedialdatabaselib.constants import (
    DEFAULT_MEDIA_CSV_PATH,
    DEFAULT_LIMITS_CSV_PATH,
    DEFAULT_PHOTO_DIR,
    DEFAULT_VIDEO_DIR,
    DEFAULT_EDIT_PHOTO_DIR,
    DEFAULT_EDIT_VIDEO_DIR,
    DEFAULT_LOG_DIR
)
from updatemedialdatabaselib.exif_downloader import ensure_exiftool
from updatemedialdatabaselib.media_processor import process_media_file

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update media database with photo and video metadata."
    )
    parser.add_argument("--media_csv", type=str, default=DEFAULT_MEDIA_CSV_PATH,
                        help="Path to the media CSV database (PhotoMediaTest.csv)")
    parser.add_argument("--limits_csv", type=str, default=DEFAULT_LIMITS_CSV_PATH,
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
    # ExifTool path is now managed via constants, no longer a parameter
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
        exiftool_path = ensure_exiftool()
        logging.debug(f"Using ExifTool at: {exiftool_path}")
    except Exception as e:
        logging.error(f"Failed to ensure ExifTool: {e}")
        return
    
    # Load existing database
    try:
        database = load_csv(args.media_csv)
        logging.debug(f"Loaded {len(database)} records from media database")
    except Exception as e:
        logging.error(f"Failed to load media database: {e}")
        database = []
    
    # Load limits
    try:
        limits = load_csv(args.limits_csv)
        logging.debug(f"Loaded {len(limits)} photo bank limits")
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
        
        print(f"Processing directory: {directory}")
        logging.debug(f"Processing directory: {directory}")
        
        # Get all files in the directory
        files = list_files(directory, recursive=True)
        print(f"Found {len(files)} files in {directory}")
        logging.debug(f"Found {len(files)} files in {directory}")
        
        # Process each file with progress bar
        if files:
            with tqdm(files, desc=f"Processing {os.path.basename(directory)}", unit="file") as pbar:
                for file_path in pbar:
                    pbar.set_postfix_str(f"Current: {os.path.basename(file_path)}")
                    record = process_media_file(file_path, database, limits, exiftool_path)
                    if record:
                        new_records.append(record)
    
    # Update database with new records
    if new_records:
        print(f"\nAdding {len(new_records)} new records to database")
        logging.debug(f"Adding {len(new_records)} new records to database")
        updated_database = database + new_records
        
        # Save updated database
        try:
            print("Saving updated database...")
            save_csv(args.media_csv, updated_database, backup=True)
            print(f"✅ Successfully saved database with {len(updated_database)} total records")
            logging.debug(f"Saved updated database with {len(updated_database)} records")
        except Exception as e:
            logging.error(f"Failed to save database: {e}")
            print(f"❌ Failed to save database: {e}")
    else:
        print("No new records found to add to database")
        logging.debug("No new records to add to database")
    
    print("\n✅ UpdateMediaDatabase completed successfully")
    logging.info("UpdateMediaDatabase completed successfully")

if __name__ == "__main__":
    main()
