#!/usr/bin/env python
"""
Prepare Media File - GUI tool for editing metadata of a single media file.

This module provides a GUI dialog for editing metadata of individual media files.
It allows users to modify titles, descriptions, keywords, and categories for photobank submission.
"""
import argparse
import json
import logging
import os
import sys
from typing import Any

from givephotobankreadymediafileslib.constants import (
    DEFAULT_CATEGORIES_CSV_PATH,
    DEFAULT_LOGS_DIR,
    DEFAULT_TRAINING_DATA_DIR,
)
from givephotobankreadymediafileslib.gui.editor_dialog import EditorDialog
from PyQt5.QtWidgets import QApplication
from shared.file_operations import ensure_directory
from shared.logging_config import setup_logging


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    :returns: Parsed command line arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="Prepare media file for photobanks.")
    parser.add_argument("--file", type=str, help="Path to the media file")
    parser.add_argument("--record", type=str, help="JSON string with record data")
    parser.add_argument(
        "--categories_file", type=str, default=DEFAULT_CATEGORIES_CSV_PATH, help="Path to the categories CSV file"
    )
    parser.add_argument(
        "--training_data_dir", type=str, default=DEFAULT_TRAINING_DATA_DIR, help="Directory for storing training data"
    )
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOGS_DIR, help="Directory for log files")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


def main() -> int:
    """Main function.

    Entry point for the media file preparation tool. Validates input file,
    sets up logging, and launches the metadata editor dialog.

    :returns: Exit code (0 for success, 1 for failure)
    :rtype: int
    """
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = os.path.join(args.log_dir, "preparemediafile.log")
    setup_logging(debug=args.debug, log_file=log_file)

    # Log startup
    logging.info("Starting preparemediafile.py")

    # Check if file is provided
    if not args.file:
        logging.error("No file provided")
        print("Error: No file provided. Use --file argument.")
        return 1

    # Check if file exists
    if not os.path.exists(args.file):
        logging.error(f"File not found: {args.file}")
        print(f"Error: File not found: {args.file}")
        return 1

    # Parse record data if provided
    record = None
    if args.record:
        try:
            record = json.loads(args.record)
            logging.info(f"Loaded record data: {record}")
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing record data: {e}")
            print(f"Error: Invalid record data: {e}")
            return 1

    # Ensure training data directory exists
    ensure_directory(args.training_data_dir)

    # Start the application
    app = QApplication(sys.argv)

    # Create and show the editor dialog
    dialog = EditorDialog(
        file_path=args.file,
        record=record,
        categories_file=args.categories_file,
        training_data_dir=args.training_data_dir,
    )

    # Connect to the metadata_saved signal
    def on_metadata_saved(metadata: dict[str, Any]) -> None:
        """Handle metadata saved signal.

        :param metadata: The saved metadata dictionary
        :type metadata: Dict[str, Any]
        :returns: None
        :rtype: None
        """
        # Print the metadata as JSON to stdout
        print(json.dumps(metadata, ensure_ascii=False))

    dialog.metadata_saved.connect(on_metadata_saved)

    # Show the dialog
    result = dialog.exec_()

    # Return success if dialog was accepted
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
