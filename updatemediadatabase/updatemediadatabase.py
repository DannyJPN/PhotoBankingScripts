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
from shared.file_operations import ensure_directory, list_files, load_csv, save_csv_with_backup
from shared.logging_config import setup_logging
from tqdm import tqdm

# Import project-specific modules
from updatemedialdatabaselib.constants import (
    DEFAULT_MEDIA_CSV_PATH,
    DEFAULT_LIMITS_CSV_PATH,
    DEFAULT_PHOTO_DIR,
    DEFAULT_VIDEO_DIR,
    DEFAULT_EDIT_PHOTO_DIR,
    DEFAULT_EDIT_VIDEO_DIR,
    DEFAULT_LOG_DIR,
    COLUMN_FILENAME
)
from updatemedialdatabaselib.exif_downloader import ensure_exiftool
from updatemedialdatabaselib.media_processor import process_media_file

def apply_jpg_first_logic(all_files: List[str]) -> List[str]:
    """
    Apply JPG-first logic to file list.
    
    Rules:
    1. Always include JPG files
    2. For non-JPG files, include only if no JPG with same basename exists
    
    Args:
        all_files: List of all file paths
        
    Returns:
        Filtered list of files to process
    """
    import os
    from collections import defaultdict
    
    # Group files by basename (without extension)
    files_by_basename = defaultdict(list)
    
    for file_path in all_files:
        basename = os.path.splitext(os.path.basename(file_path))[0]
        files_by_basename[basename].append(file_path)
    
    files_to_process = []
    
    for basename, file_paths in files_by_basename.items():
        # Check if any JPG files exist for this basename
        jpg_files = [f for f in file_paths if f.lower().endswith(('.jpg', '.jpeg'))]
        
        if jpg_files:
            # If JPG files exist, add all JPG files
            files_to_process.extend(jpg_files)
            logging.debug(f"Added {len(jpg_files)} JPG files for basename '{basename}'")
        else:
            # If no JPG files, add all non-JPG files for this basename
            files_to_process.extend(file_paths)
            logging.debug(f"Added {len(file_paths)} non-JPG files for basename '{basename}' (no JPG found)")
    
    return files_to_process

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

    # Extract filenames from database for efficient lookup
    existing_filenames = set()
    for record in database:
        filename = record.get(COLUMN_FILENAME)
        if filename:
            existing_filenames.add(filename)
    logging.debug(f"Extracted {len(existing_filenames)} existing filenames for lookup")
    
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
    
    # Process each directory with JPG-first logic
    new_records = []
    for directory in media_dirs:
        if not os.path.exists(directory):
            logging.warning(f"Directory does not exist, skipping: {directory}")
            continue
        
        print(f"Processing directory: {directory}")
        logging.debug(f"Processing directory: {directory}")
        
        # Get all files in the directory
        all_files = list_files(directory, recursive=True)
        print(f"Found {len(all_files)} files in {directory}")
        logging.debug(f"Found {len(all_files)} files in {directory}")
        
        if not all_files:
            continue
            
        # Apply JPG-first logic: prioritize JPG files, add non-JPG only if no JPG with same basename exists
        files_to_process = apply_jpg_first_logic(all_files)
        print(f"After JPG-first filtering: {len(files_to_process)} files to process")
        logging.debug(f"After JPG-first filtering: {len(files_to_process)} files to process")
        
        # Process filtered files with progress bar
        with tqdm(files_to_process, desc=f"Processing {os.path.basename(directory)}", unit="file") as pbar:
            for file_path in pbar:
                pbar.set_postfix_str(f"Current: {os.path.basename(file_path)}")
                record = process_media_file(file_path, database, limits, exiftool_path, existing_filenames)
                if record:
                    new_records.append(record)
                    # Add to existing filenames to prevent processing duplicates within this run
                    existing_filenames.add(record.get(COLUMN_FILENAME))
    
    # Update database with new records
    if new_records:
        print(f"\nAdding {len(new_records)} new records to database")
        logging.debug(f"Adding {len(new_records)} new records to database")
        updated_database = database + new_records
        
        # Save updated database
        try:
            print("Saving updated database...")
            save_csv_with_backup(updated_database, args.media_csv)
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
