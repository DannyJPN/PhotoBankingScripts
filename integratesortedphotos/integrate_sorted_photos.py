#!/usr/bin/env python
"""
Integrate Sorted Photos - Script for integrating sorted photos into target directory.

This script copies sorted photos from one directory to another while preserving
file dates and directory structure.
"""
import argparse
import logging
import os

from integratesortedphotoslib.constants import DEFAULT_SORTED_FOLDER, DEFAULT_TARGET_FOLDER, LOG_DIR
from integratesortedphotoslib.copy_files import copy_files_with_preserved_dates
from shared.logging_config import setup_logging
from shared.utils import get_log_filename


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    :returns: Parsed command line arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="Integrate sorted photos from one directory to another.")
    parser.add_argument(
        "--sortedFolder", type=str, nargs="?", default=DEFAULT_SORTED_FOLDER, help="Path to the sorted folder."
    )
    parser.add_argument(
        "--targetFolder", type=str, nargs="?", default=DEFAULT_TARGET_FOLDER, help="Path to the target folder."
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    return parser.parse_args()


def main() -> None:
    """Main function for integrating sorted photos.

    :returns: None
    :rtype: None
    """
    args = parse_arguments()
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Generate the log filename
    LOG_FILE = get_log_filename(LOG_DIR)

    # Setup logging with the log file path
    setup_logging(args.debug, LOG_FILE)

    logging.info(f"SortedFolder: {args.sortedFolder}")
    logging.info(f"TargetFolder: {args.targetFolder}")
    logging.info(f"LogFile: {LOG_FILE}")

    # Ensure the paths are valid
    if not os.path.exists(args.sortedFolder):
        logging.error(f"SortedFolder does not exist: {args.SortedFolder}")
        return

    log_dir = os.path.dirname(LOG_FILE)
    if LOG_FILE and not os.path.exists(log_dir):
        os.makedirs(log_dir)
        logging.info(f"Created log directory: {log_dir}")

    # Call the copy function
    copy_files_with_preserved_dates(args.sortedFolder, args.targetFolder)


if __name__ == "__main__":
    main()
