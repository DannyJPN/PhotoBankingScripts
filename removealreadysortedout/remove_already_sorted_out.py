import argparse
import logging
from tqdm import tqdm

from shared.utils import get_log_filename
from shared.file_operations import list_files, ensure_directory, unify_duplicate_files
from shared.logging_config import setup_logging

from removealreadysortedoutlib.constants import (
    DEFAULT_UNSORTED_FOLDER,
    DEFAULT_TARGET_FOLDER,
    DEFAULT_LOG_DIR,
)

from removealreadysortedoutlib.removal_operations import (
    get_target_hash_map,
    find_duplicates,
    handle_duplicate,
    remove_desktop_ini,
)

from removealreadysortedoutlib.renaming import replace_in_filenames


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Remove files from unsorted folder that already exist in target folder."
    )
    parser.add_argument("--unsorted_folder", type=str, default=DEFAULT_UNSORTED_FOLDER,
                        help="Source folder with unsorted files")
    parser.add_argument("--target_folder", type=str, default=DEFAULT_TARGET_FOLDER,
                        help="Target folder with sorted files")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    return parser.parse_args()


def main():
    args = parse_arguments()

    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    logging.info("Starting RemoveAlreadySortedOut process")
    logging.info("Unsorted folder: %s", args.unsorted_folder)
    logging.info("Target folder: %s", args.target_folder)

    # Remove desktop.ini if it exists
    remove_desktop_ini(args.unsorted_folder)

    # Step 1: Unify duplicate files in both folders
    logging.info("Step 1: Unifying duplicate files...")
    unify_duplicate_files(args.unsorted_folder, recursive=True)
    unify_duplicate_files(args.target_folder, recursive=True)

    # Step 2: Generic filename replacements (_NIK -> NIK_ by default)
    logging.info("Step 2: Replacing filename patterns...")
    replace_in_filenames(args.unsorted_folder, "_NIK", "NIK_", recursive=True)
    replace_in_filenames(args.target_folder, "_NIK", "NIK_", recursive=True)

    # Step 3: Build content-hash map of target folder
    logging.info("Step 3: Building hash map of target folder...")
    target_hash_map = get_target_hash_map(args.target_folder)
    logging.info("Found %d unique file hashes in target folder", len(target_hash_map))

    # Step 4: List files in unsorted folder
    logging.info("Step 4: Listing files in unsorted folder...")
    unsorted_files = list_files(args.unsorted_folder, recursive=True)
    logging.info("Found %d files in unsorted folder", len(unsorted_files))

    # Step 5: Find duplicates by content hash
    logging.info("Step 5: Finding duplicates...")
    duplicates = find_duplicates(unsorted_files, target_hash_map)
    logging.info("Found %d files that exist in both folders", len(duplicates))

    # Step 6: Remove duplicates
    logging.info("Step 6: Removing duplicates...")
    with tqdm(total=len(duplicates), desc="Removing duplicates", unit="files") as pbar:
        for source_path, target_paths in duplicates.items():
            handle_duplicate(source_path, target_paths)
            pbar.update(1)

    logging.info("RemoveAlreadySortedOut process completed successfully")


if __name__ == "__main__":
    main()