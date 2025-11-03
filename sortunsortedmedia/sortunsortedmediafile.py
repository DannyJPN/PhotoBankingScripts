
#!/usr/bin/env python3
"""
Script for processing and sorting a single media file.
"""

import os
import sys
import argparse
import logging
import time
from datetime import datetime
from typing import Optional

from shared.utils import get_log_filename
from shared.file_operations import ensure_directory, move_file
from shared.logging_config import setup_logging
from shared.exif_handler import get_best_creation_date

from sortunsortedmedialib.constants import DEFAULT_TARGET_FOLDER, TERMINAL_PAUSE_DURATION, RAW_EXTENSIONS
from sortunsortedmedialib.media_classifier import classify_media_file
from sortunsortedmedialib.interactive import ask_for_category
from sortunsortedmedialib.path_builder import build_target_path, build_edited_target_path, ensure_unique_path
from sortunsortedmedialib.companion_file_finder import find_jpg_equivalent, find_original_file, extract_metadata_from_path

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process and sort a single media file."
    )
    parser.add_argument("--media_file", type=str, required=True,
                        help="Path to the media file to process")
    parser.add_argument("--target_folder", type=str, default=DEFAULT_TARGET_FOLDER,
                        help="Target folder for sorted media")
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

        # DECISION LOGIC: Determine if we need user categorization or can use existing metadata
        needs_categorization = True
        metadata_from_original = None

        # Case A: JPG or Video → always categorize
        if extension.lower() in ['jpg', 'jpeg'] or media_type == "Video":
            logging.debug(f"File is JPG or Video - requiring categorization")
            needs_categorization = True

        # Case B: Alternative format (PNG, RAW, TIFF, etc.)
        elif not is_edited and media_type == "Foto":
            logging.debug(f"File is alternative image format ({extension}) - searching for JPG equivalent")
            jpg_path = find_jpg_equivalent(filename, target_folder)

            if jpg_path:
                # Found JPG equivalent → skip GUI, use its metadata
                logging.info(f"Found JPG equivalent: {jpg_path}")
                metadata_from_original = extract_metadata_from_path(jpg_path)
                needs_categorization = False
            else:
                # No JPG equivalent → process as JPG (with GUI)
                logging.info(f"No JPG equivalent found - processing as new file")
                needs_categorization = True

        # Case C: Edited file
        elif is_edited:
            logging.debug(f"File is edited - searching for original")
            is_video = (media_type == "Video")
            original_path = find_original_file(filename, target_folder, is_video)

            if original_path:
                # Found original → skip GUI, use its metadata
                logging.info(f"Found original file: {original_path}")
                metadata_from_original = extract_metadata_from_path(original_path)
                needs_categorization = False
            else:
                # No original → process as new edited file (with GUI)
                logging.info(f"No original found - processing as new edited file")
                needs_categorization = True

        # Get category and camera
        if needs_categorization:
            # Preload RAW file if needed (BEFORE opening GUI)
            preloaded_image = None
            if os.path.splitext(media_path)[1].lower() in RAW_EXTENSIONS:
                logging.info(f"Preloading RAW file before GUI: {media_path}")
                print(f"Loading RAW file (this may take a few seconds)...")
                try:
                    import rawpy
                    from PIL import Image
                    with rawpy.imread(media_path) as raw:
                        rgb = raw.postprocess(
                            use_camera_wb=True,
                            use_auto_wb=False,
                            output_bps=8,
                            no_auto_bright=True,
                            output_color=rawpy.ColorSpace.sRGB
                        )
                        preloaded_image = Image.fromarray(rgb)
                        logging.info(f"RAW file preloaded successfully: {preloaded_image.size}")
                        print(f"RAW file loaded, opening GUI...")
                except ImportError:
                    logging.warning("rawpy not available - GUI will load thumbnail only")
                except Exception as e:
                    logging.warning(f"Failed to preload RAW: {e}, GUI will load thumbnail")

            # Show GUI to get category and camera from user
            from sortunsortedmedialib.media_viewer import show_media_viewer

            # Variables to store user selection
            selected_category = None
            selected_camera = None

            def completion_callback(cat: str, cam: str):
                nonlocal selected_category, selected_camera
                selected_category = cat
                selected_camera = cam

            # Show GUI with preloaded image (if available)
            logging.info(f"Showing GUI for user categorization of {filename}")
            show_media_viewer(media_path, target_folder, completion_callback, preloaded_image=preloaded_image)

            # Use the selected values or defaults
            category = selected_category if selected_category else "Ostatní"
            if selected_camera and selected_camera != "Unknown":
                camera = selected_camera
        else:
            # Use metadata from original/companion file
            category = metadata_from_original.get('category', 'Ostatní')
            camera = metadata_from_original.get('camera_name', camera)
            logging.info(f"Using metadata from companion file: category={category}, camera={camera}")

        # Build target directory path
        if is_edited:
            # Edited files go to "Upravené Foto" or "Upravené Video"
            target_dir = build_edited_target_path(
                base_folder=target_folder,
                media_type=media_type,
                extension=extension,
                category=category,
                date=creation_date,
                camera_name=camera
            )
        else:
            # Regular files go to "Foto" or "Video"
            target_dir = build_target_path(
                base_folder=target_folder,
                media_type=media_type,
                extension=extension,
                category=category,
                date=creation_date,
                camera_name=camera,
                is_edited=False,
                edit_type=""
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
        print(f"\n{'='*80}")
        print(f"SUCCESS: File has been moved to:")
        print(f"{result_path}")
        print(f"{'='*80}")
    else:
        logging.error(f"Failed to process media file: {args.media_file}")
        print(f"\n{'='*80}")
        print(f"ERROR: Failed to process media file")
        print(f"{'='*80}")

    logging.info("Media file processing completed")

    # Keep terminal open for TERMINAL_PAUSE_DURATION seconds to allow user to see the result
    pause_minutes = TERMINAL_PAUSE_DURATION // 60
    pause_seconds = TERMINAL_PAUSE_DURATION % 60

    if pause_minutes > 0:
        if pause_seconds > 0:
            print(f"\nThis window will close automatically in {pause_minutes} minute(s) and {pause_seconds} second(s).")
        else:
            print(f"\nThis window will close automatically in {pause_minutes} minute(s).")
    else:
        print(f"\nThis window will close automatically in {pause_seconds} second(s).")

    print("You can close this window manually at any time by pressing Ctrl+C or clicking the X button.")

    try:
        time.sleep(TERMINAL_PAUSE_DURATION)
    except KeyboardInterrupt:
        print("\n\nWindow closed by user.")
        logging.info("Terminal pause interrupted by user")

if __name__ == "__main__":
    main()
