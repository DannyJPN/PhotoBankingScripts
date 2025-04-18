import argparse
import logging
import os
import sys
from shared.logging_config import setup_logging
from shared.utils import get_log_filename
from removealreadysortedoutlib.unify_files import unify_files
from removealreadysortedoutlib.get_file_paths import get_file_paths
from removealreadysortedoutlib.find_already_sorted_files import find_already_sorted_files
from removealreadysortedoutlib.remove_sorted_files import remove_sorted_files
from removealreadysortedoutlib.rename_files import rename_files
from removealreadysortedoutlib.constants import LOG_DIR
from removealreadysortedoutlib.handle_pict_files import handle_pict_files

def main():
    # Define input parameters
    parser = argparse.ArgumentParser(description="RemoveAlreadySortedOut Script")
    parser.add_argument("--unsorted-folder", type=str, default="I:/NeroztĹ™Ă­dÄ›noTest", help="Path to the unsorted folder")
    parser.add_argument("--target-folder", type=str, default="J:/FotoJPG", help="Path to the target folder")
    parser.add_argument("--debug", action="store_true", help="Enable debug level logging")

    # Parse input parameters
    args = parser.parse_args()
    # Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Generate the log filename
    log_file = get_log_filename(LOG_DIR)

    # Setup logging with the log file path
    setup_logging(args.debug, log_file)

    # Log the start of the script
    logging.info("Starting RemoveAlreadySortedOut script")
    logging.debug(f"Unsorted folder: {args.unsorted_folder}")
    logging.debug(f"Target folder: {args.target_folder}")
    logging.debug(f"Log file: {log_file}")

    # Log current working directory and contents of shared directory
    logging.debug(f"Current working directory: {os.getcwd()}")
    logging.debug(f"Python path: {sys.path}")
    logging.debug(f"Contents of shared directory: {os.listdir('shared')}")

    # Step 1: Rename files
    rename_files(args.unsorted_folder)

    # Step 2: Handle PICT files
    handle_pict_files(args.unsorted_folder, args.target_folder)

    # Step 3: Unify files
    unify_files(args.unsorted_folder)

    # Step 4: Find already sorted files
    already_sorted = find_already_sorted_files(args.unsorted_folder, args.target_folder)
    logging.debug(f"Already sorted files: {already_sorted}")

    # Step 5: Remove sorted files
    remove_sorted_files(already_sorted)

if __name__ == "__main__":
    main()
