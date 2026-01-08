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
    DEFAULT_REPORT_DIR,
    DEFAULT_REPORT_FORMAT,
    COLUMN_FILENAME
)
from updatemedialdatabaselib.exif_downloader import ensure_exiftool
from updatemedialdatabaselib.media_processor import process_media_file

def split_files_by_type(all_files: List[str]) -> Dict[str, List[str]]:
    """
    Split files into JPG, non-JPG images, and videos.

    Args:
        all_files: List of all file paths

    Returns:
        Dictionary with keys 'jpg', 'non_jpg_images', 'videos' containing file lists
    """
    jpg_files = []
    non_jpg_images = []
    videos = []

    # Extensions for each category
    JPG_EXTENSIONS = ('.jpg', '.jpeg')
    VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi', '.wmv', '.mkv')
    IMAGE_EXTENSIONS = ('.png', '.tif', '.tiff', '.dng', '.nef', '.raw', '.cr2', '.arw', '.psd')

    for file_path in all_files:
        ext = os.path.splitext(file_path)[1].lower()

        if ext in JPG_EXTENSIONS:
            jpg_files.append(file_path)
        elif ext in VIDEO_EXTENSIONS:
            videos.append(file_path)
        elif ext in IMAGE_EXTENSIONS:
            non_jpg_images.append(file_path)
        else:
            logging.debug(f"Skipping file with unknown extension: {file_path}")

    logging.debug(f"Split files: {len(jpg_files)} JPG, {len(non_jpg_images)} non-JPG images, {len(videos)} videos")
    return {
        'jpg': jpg_files,
        'non_jpg_images': non_jpg_images,
        'videos': videos
    }

def get_basename_from_filepath(file_path: str) -> str:
    """
    Get basename (filename without extension) from file path.

    Args:
        file_path: Full file path

    Returns:
        Basename without extension
    """
    return os.path.splitext(os.path.basename(file_path))[0]

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update media database with photo and video metadata."
    )
    parser.add_argument("--media_csv", type=str, default=DEFAULT_MEDIA_CSV_PATH,
                        help="Path to the media CSV database (PhotoMedia.csv)")
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
    parser.add_argument(\"--export-report\", action=\"store_true\",
                        help=\"Export summary report of processed records\")
    parser.add_argument(\"--report-dir\", type=str, default=DEFAULT_REPORT_DIR,
                        help=\"Directory for report output\")
    parser.add_argument(\"--report-format\", type=str, default=DEFAULT_REPORT_FORMAT,
                        choices=[\"csv\", \"json\"], help=\"Report format: csv or json\")
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

    # Step 1: Collect all files from all directories
    print("Collecting files from all directories...")
    all_files = []
    for directory in media_dirs:
        if not os.path.exists(directory):
            logging.warning(f"Directory does not exist, skipping: {directory}")
            continue

        print(f"Scanning directory: {directory}")
        logging.debug(f"Scanning directory: {directory}")

        # Get all files in the directory
        dir_files = list_files(directory, recursive=True)
        all_files.extend(dir_files)
        print(f"Found {len(dir_files)} files in {directory}")
        logging.debug(f"Found {len(dir_files)} files in {directory}")

    print(f"\nTotal files found: {len(all_files)}")
    logging.info(f"Total files found: {len(all_files)}")

    if not all_files:
        print("No files found to process")
        logging.info("No files found to process")
        return

    # Step 2: Split files by type (JPG, videos, non-JPG images)
    print("Splitting files by type...")
    files_by_type = split_files_by_type(all_files)
    jpg_files = files_by_type['jpg']
    videos = files_by_type['videos']
    non_jpg_images = files_by_type['non_jpg_images']

    print(f"  JPG files: {len(jpg_files)}")
    print(f"  Videos: {len(videos)}")
    print(f"  Non-JPG images: {len(non_jpg_images)}")
    logging.info(f"Split files: {len(jpg_files)} JPG, {len(videos)} videos, {len(non_jpg_images)} non-JPG images")

    report_stats = {
        "new_jpg": 0,
        "new_video": 0,
        "new_non_jpg": 0,
        "skipped_non_jpg": 0,
        "updated": 0
    }

    # Step 3: Process JPG files first
    if jpg_files:
        print("\n=== Phase 1: Processing JPG files ===")
        logging.info("Phase 1: Processing JPG files")
        new_records = []

        with tqdm(jpg_files, desc="Processing JPG files", unit="file") as pbar:
            for file_path in pbar:
                pbar.set_postfix_str(f"Current: {os.path.basename(file_path)}")
                record = process_media_file(file_path, database, limits, exiftool_path, existing_filenames)
                if record:
                    new_records.append(record)
                    existing_filenames.add(record.get(COLUMN_FILENAME))

        if new_records:
            print(f"Adding {len(new_records)} JPG records to database")
            logging.info(f"Adding {len(new_records)} JPG records to database")
            database = database + new_records

            try:
                print("Saving database after JPG processing...")
                save_csv_with_backup(database, args.media_csv)
                print(f"✅ Saved database with {len(database)} total records")
                logging.info(f"Saved database with {len(database)} records after JPG phase")
            except Exception as e:
                logging.error(f"Failed to save database after JPG phase: {e}")
                print(f"❌ Failed to save database: {e}")
                return

            # Reload database to ensure we have the latest data
            try:
                database = load_csv(args.media_csv)
                existing_filenames = set(record.get(COLUMN_FILENAME) for record in database if record.get(COLUMN_FILENAME))
                logging.debug(f"Reloaded database: {len(database)} records, {len(existing_filenames)} filenames")
            except Exception as e:
                logging.error(f"Failed to reload database: {e}")
        else:
            print("No new JPG records to add")
            logging.info("No new JPG records")

    # Step 4: Process videos
    if videos:
        print("\n=== Phase 2: Processing videos ===")
        logging.info("Phase 2: Processing videos")
        new_records = []

        with tqdm(videos, desc="Processing videos", unit="file") as pbar:
            for file_path in pbar:
                pbar.set_postfix_str(f"Current: {os.path.basename(file_path)}")
                record = process_media_file(file_path, database, limits, exiftool_path, existing_filenames)
                if record:
                    new_records.append(record)
                    existing_filenames.add(record.get(COLUMN_FILENAME))

        if new_records:
            print(f"Adding {len(new_records)} video records to database")
            logging.info(f"Adding {len(new_records)} video records to database")
            database = database + new_records

            try:
                print("Saving database after video processing...")
                save_csv_with_backup(database, args.media_csv)
                print(f"✅ Saved database with {len(database)} total records")
                logging.info(f"Saved database with {len(database)} records after video phase")
            except Exception as e:
                logging.error(f"Failed to save database after video phase: {e}")
                print(f"❌ Failed to save database: {e}")
                return

            # Reload database
            try:
                database = load_csv(args.media_csv)
                existing_filenames = set(record.get(COLUMN_FILENAME) for record in database if record.get(COLUMN_FILENAME))
                logging.debug(f"Reloaded database: {len(database)} records, {len(existing_filenames)} filenames")
            except Exception as e:
                logging.error(f"Failed to reload database: {e}")
        else:
            print("No new video records to add")
            logging.info("No new video records")

    # Step 5: Process non-JPG images (only if JPG version doesn't exist in DB)
    if non_jpg_images:
        print("\n=== Phase 3: Processing non-JPG images ===")
        logging.info("Phase 3: Processing non-JPG images")

        # Build a set of basenames from existing JPG files in database
        jpg_basenames_in_db = set()
        for record in database:
            filename = record.get(COLUMN_FILENAME)
            if filename and filename.lower().endswith(('.jpg', '.jpeg')):
                basename = get_basename_from_filepath(filename)
                jpg_basenames_in_db.add(basename)

        logging.debug(f"Found {len(jpg_basenames_in_db)} JPG basenames in database")

        # Filter non-JPG files: skip if JPG version exists
        files_to_process = []
        skipped_count = 0
        for file_path in non_jpg_images:
            basename = get_basename_from_filepath(file_path)
            if basename in jpg_basenames_in_db:
                logging.debug(f"Skipping {os.path.basename(file_path)} - JPG version exists in database")
                skipped_count += 1
            else:
                files_to_process.append(file_path)

        print(f"  Files to process: {len(files_to_process)}")
        print(f"  Files skipped (JPG exists): {skipped_count}")
        logging.info(f"Non-JPG: {len(files_to_process)} to process, {skipped_count} skipped (JPG exists)")
        report_stats["skipped_non_jpg"] = skipped_count

        if files_to_process:
            new_records = []

            with tqdm(files_to_process, desc="Processing non-JPG images", unit="file") as pbar:
                for file_path in pbar:
                    pbar.set_postfix_str(f"Current: {os.path.basename(file_path)}")
                    record = process_media_file(file_path, database, limits, exiftool_path, existing_filenames)
                    if record:
                        new_records.append(record)
                        existing_filenames.add(record.get(COLUMN_FILENAME))

            if new_records:
                print(f"Adding {len(new_records)} non-JPG records to database")
                logging.info(f"Adding {len(new_records)} non-JPG records to database")
                database = database + new_records

                try:
                    print("Saving database after non-JPG processing...")
                    save_csv_with_backup(database, args.media_csv)
                    print(f"✅ Saved database with {len(database)} total records")
                    logging.info(f"Saved database with {len(database)} records after non-JPG phase")
                except Exception as e:
                    logging.error(f"Failed to save database after non-JPG phase: {e}")
                    print(f"❌ Failed to save database: {e}")
                    return
            else:
                print("No new non-JPG records to add")
                logging.info("No new non-JPG records")
        else:
            print("No non-JPG files to process (all have JPG versions)")
            logging.info("No non-JPG files to process")
    
    print("\n✅ UpdateMediaDatabase completed successfully")
    if args.export_report:
        _write_report(report_stats, args.report_dir, args.report_format)

    logging.info("UpdateMediaDatabase completed successfully")

def _write_report(stats: Dict[str, int], report_dir: str, report_format: str) -> None:
    """
    Write summary report for processed records.
    """
    from datetime import datetime
    from shared.file_operations import save_csv, save_json
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"UpdateMediaDatabaseReport_{timestamp}.{report_format}"
    report_path = os.path.join(report_dir, filename)
    records = [{"metric": key, "count": str(value)} for key, value in stats.items()]
    if report_format == "csv":
        save_csv(records, report_path, ["metric", "count"])
    else:
        save_json({"metrics": records}, report_path)
    logging.info("Report saved to %s", report_path)


if __name__ == "__main__":
    main()
