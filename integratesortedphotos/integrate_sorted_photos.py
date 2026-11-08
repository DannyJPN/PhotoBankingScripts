import os
import logging
import argparse
from shared.logging_config import setup_logging
from integratesortedphotoslib.constants import DEFAULT_SORTED_FOLDER, DEFAULT_TARGET_FOLDER, DEFAULT_LOG_DIR
from integratesortedphotoslib.copy_files import copy_files_with_preserved_dates
from shared.utils import get_log_filename
from shared.file_operations import ensure_directory

def parse_arguments():
    parser = argparse.ArgumentParser(description="Integrate sorted photos from one directory to another.")
    parser.add_argument('--sortedFolder', type=str, nargs='?', default=DEFAULT_SORTED_FOLDER, help="Path to the sorted folder.")
    parser.add_argument('--targetFolder', type=str, nargs='?', default=DEFAULT_TARGET_FOLDER, help="Path to the target folder.")
    parser.add_argument('--log_dir', type=str, default=DEFAULT_LOG_DIR, help="Directory for log files")
    parser.add_argument('--debug', action='store_true', help="Enable debug mode.")
    parser.add_argument('--conflict-strategy', type=str, default='skip',
                        choices=['skip', 'overwrite', 'rename'],
                        help="Conflict strategy: skip, overwrite, rename")
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)
    
    logging.info("Starting integrate sorted photos")
    logging.info(f"SortedFolder: {args.sortedFolder}")
    logging.info(f"TargetFolder: {args.targetFolder}")

    # Ensure the paths are valid
    if not os.path.exists(args.sortedFolder):
        logging.error(f"SortedFolder does not exist: {args.sortedFolder}")
        return

    # Call the copy function
    copy_files_with_preserved_dates(args.sortedFolder, args.targetFolder, args.conflict_strategy)

if __name__ == '__main__':
    main()
