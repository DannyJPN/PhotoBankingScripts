import argparse
import logging

from removealreadysortedoutlib.constants import DEFAULT_LOG_DIR, DEFAULT_TARGET_FOLDER, DEFAULT_UNSORTED_FOLDER
from removealreadysortedoutlib.duplicate_handler import (
    find_duplicates,
    get_target_files_map,
    handle_duplicate,
    remove_desktop_ini,
)
from removealreadysortedoutlib.gui import resolve_duplicate_gui
from shared.file_operations import ensure_directory, list_files
from shared.logging_config import setup_logging
from shared.utils import get_log_filename
from tqdm import tqdm


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Remove files from unsorted folder that already exist in target folder."
    )
    parser.add_argument(
        "--unsorted_folder", type=str, default=DEFAULT_UNSORTED_FOLDER, help="Source folder with unsorted files"
    )
    parser.add_argument(
        "--target_folder", type=str, default=DEFAULT_TARGET_FOLDER, help="Target folder with sorted files"
    )
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR, help="Directory for log files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite files with different sizes")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main():
    # Parse command line arguments
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    logging.info("Starting RemoveAlreadySortedOut process")
    logging.info(f"Unsorted folder: {args.unsorted_folder}")
    logging.info(f"Target folder: {args.target_folder}")
    logging.info(f"Overwrite mode: {args.overwrite}")

    # Remove desktop.ini if it exists
    remove_desktop_ini(args.unsorted_folder)

    # Get list of files from unsorted folder
    logging.info("Listing files in unsorted folder...")
    unsorted_files = list_files(args.unsorted_folder, recursive=True)
    logging.info(f"Found {len(unsorted_files)} files in unsorted folder")

    # Get map of files in target folder
    logging.info("Building map of files in target folder...")
    target_files_map = get_target_files_map(args.target_folder)
    logging.info(f"Found {len(target_files_map)} unique filenames in target folder")

    # Find duplicates
    logging.info("Finding duplicates...")
    duplicates = find_duplicates(unsorted_files, target_files_map)
    logging.info(f"Found {len(duplicates)} files that exist in both folders")

    # Process duplicates
    logging.info("Processing duplicates...")
    for source_path, target_paths in tqdm(duplicates.items(), desc="Processing duplicates", unit="file"):
        # Always use GUI for resolving duplicates with different content
        handle_duplicate(source_path, target_paths, args.overwrite, log_file, gui_handler=resolve_duplicate_gui)

    logging.info("RemoveAlreadySortedOut process completed successfully")


if __name__ == "__main__":
    main()
