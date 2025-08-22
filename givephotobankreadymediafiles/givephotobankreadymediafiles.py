#!/usr/bin/env python
"""
Give Photobank Ready Media Files - Batch processing tool for preparing media files for photobanks.

This module provides a GUI application for batch processing media files for photobank submission.
It performs system checks, validates required files, and launches the main processing interface.
"""
import argparse
import logging
import os
import sys
from typing import Any

from givephotobankreadymediafileslib.constants import (
    DEFAULT_CATEGORIES_CSV_PATH,
    DEFAULT_INTERVAL,
    DEFAULT_LIMITS_CSV_PATH,
    DEFAULT_LOGS_DIR,
    DEFAULT_MEDIA_CSV_PATH,
    DEFAULT_PROCESSED_MEDIA_MAX_COUNT,
    DEFAULT_TRAINING_DATA_DIR,
)
from givephotobankreadymediafileslib.data_loader import load_categories_csv, load_media_csv
from givephotobankreadymediafileslib.gui.main_window import MainWindow
from givephotobankreadymediafileslib.system_checker import SystemChecker
from PyQt5.QtWidgets import QApplication, QMessageBox
from shared.file_operations import ensure_directory
from shared.logging_config import setup_logging


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    :returns: Parsed command line arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="Batch process media files for photobanks.")
    parser.add_argument("--media_csv", type=str, default=DEFAULT_MEDIA_CSV_PATH, help="Path to the media CSV file")
    parser.add_argument("--limits_csv", type=str, default=DEFAULT_LIMITS_CSV_PATH, help="Path to the limits CSV file")
    parser.add_argument(
        "--categories_csv", type=str, default=DEFAULT_CATEGORIES_CSV_PATH, help="Path to the categories CSV file"
    )
    parser.add_argument(
        "--processed_media_max_count",
        type=int,
        default=DEFAULT_PROCESSED_MEDIA_MAX_COUNT,
        help="Maximum number of media files to process",
    )
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="Interval between processing in seconds")
    parser.add_argument(
        "--training_data_dir", type=str, default=DEFAULT_TRAINING_DATA_DIR, help="Directory for storing training data"
    )
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOGS_DIR, help="Directory for log files")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


def check_system_prerequisites(
    media_csv_path: str, categories_csv_path: str, models_dir: str
) -> tuple[bool, list[str], list[str], dict[str, Any]]:
    """Check system prerequisites before starting the application.

    This function validates required files, loads CSV data, and checks for available models.
    Input files are never modified during this process.

    :param media_csv_path: Path to the media CSV file
    :type media_csv_path: str
    :param categories_csv_path: Path to the categories CSV file
    :type categories_csv_path: str
    :param models_dir: Directory containing model files
    :type models_dir: str
    :returns: Tuple of (success status, errors list, warnings list, available models dict)
    :rtype: Tuple[bool, List[str], List[str], Dict[str, Any]]
    """
    # Initialize system checker
    checker = SystemChecker()

    # Clear previous errors and warnings
    checker.clear_errors_and_warnings()

    # 1. Check if CSV files exist (critical)
    media_csv_exists = checker.check_file_exists(media_csv_path, "Media CSV")
    if not media_csv_exists:
        checker.log_results()
        return False, checker.get_errors(), checker.get_warnings(), {}

    categories_csv_exists = checker.check_file_exists(categories_csv_path, "Categories CSV")
    if not categories_csv_exists:
        checker.log_results()
        return False, checker.get_errors(), checker.get_warnings(), {}

    # 2. Load CSV files for content checks
    try:
        media_df = load_media_csv(media_csv_path)
        categories_dict = load_categories_csv(categories_csv_path)
    except Exception as e:
        checker.errors.append(f"Error loading CSV files: {e}")
        checker.log_results()
        return False, checker.get_errors(), checker.get_warnings(), {}

    # 3. Check CSV content (critical)
    media_content_ok = checker.check_media_csv_content(media_df)
    if not media_content_ok:
        checker.log_results()
        return False, checker.get_errors(), checker.get_warnings(), {}

    categories_content_ok = checker.check_categories_csv_content(categories_dict)
    # Categories content check only adds warnings, not errors

    # 4. Check unprocessed files (critical)
    files_ok = checker.check_unprocessed_files(media_df)
    if not files_ok:
        checker.log_results()
        return False, checker.get_errors(), checker.get_warnings(), {}

    # 5. Check neural networks (warning)
    nn_ok = checker.check_neural_networks(models_dir)

    # 6. Check local LLM (warning)
    local_llm_ok = checker.check_local_llm()

    # 7. Check online LLM (warning)
    online_llm_ok = checker.check_online_llm()

    # Log results
    checker.log_results()

    # Get errors and warnings
    errors = checker.get_errors()
    warnings = checker.get_warnings()

    # Get available models
    available_models = checker.get_available_models()

    # Return True if all critical checks pass
    all_ok = media_csv_exists and categories_csv_exists and media_content_ok and files_ok

    return all_ok, errors, warnings, available_models


def show_error_dialog(errors: list[str], warnings: list[str]) -> None:
    """Show error dialog with errors and warnings.

    :param errors: List of error messages to display
    :type errors: List[str]
    :param warnings: List of warning messages to display
    :type warnings: List[str]
    :returns: None
    :rtype: None
    """
    # Create error message
    error_message = "The application cannot start due to the following errors:\n\n"
    for error in errors:
        error_message += f"- {error}\n"

    if warnings:
        error_message += "\nWarnings:\n"
        for warning in warnings:
            error_message += f"- {warning}\n"

    # Show error dialog
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("System Check Failed")
    msg_box.setText(error_message)
    msg_box.exec_()


def main() -> int:
    """Main function.

    Entry point for the application. Sets up logging, validates system requirements,
    and launches the GUI interface.

    :returns: Exit code (0 for success, 1 for failure)
    :rtype: int
    """
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = os.path.join(args.log_dir, "givephotobankreadymediafiles.log")
    setup_logging(debug=args.debug, log_file=log_file)

    # Log startup
    logging.info("Starting givephotobankreadymediafiles.py")

    # Ensure directories exist
    ensure_directory(os.path.dirname(args.media_csv))
    ensure_directory(os.path.dirname(args.categories_csv))
    ensure_directory(args.training_data_dir)

    # Create empty files if they don't exist
    if not os.path.exists(args.media_csv):
        logging.warning(f"Media CSV file not found: {args.media_csv}")
        # Create an empty CSV file with English headers
        with open(args.media_csv, "w", encoding="utf-8-sig", newline="") as f:
            f.write(
                "File,Title,Description,Preparation Date,Width,Height,Resolution,Keywords,Category,Creation Date,Original,Path,Shutterstock status,Adobe status,Alamy status,Dreamstime status\n"
            )
        logging.info(f"Created empty media CSV file: {args.media_csv}")

    if not os.path.exists(args.categories_csv):
        logging.warning(f"Categories CSV file not found: {args.categories_csv}")
        # Create an empty CSV file
        with open(args.categories_csv, "w", encoding="utf-8-sig", newline="") as f:
            f.write("Shutterstock,Adobe,Alamy,Dreamstime\n")
        logging.info(f"Created empty categories CSV file: {args.categories_csv}")

    # Create application instance (needed for dialogs)
    app = QApplication(sys.argv)

    # Check system prerequisites
    models_dir = os.path.join(os.path.dirname(args.training_data_dir), "models")
    ensure_directory(models_dir)  # Ensure models directory exists

    all_ok, errors, warnings, available_models = check_system_prerequisites(
        media_csv_path=args.media_csv, categories_csv_path=args.categories_csv, models_dir=models_dir
    )

    # If checks failed, show error dialog and exit
    if not all_ok:
        show_error_dialog(errors, warnings)
        return 1

    # If there are warnings, log them
    if warnings:
        logging.warning("System check completed with warnings:")
        for warning in warnings:
            logging.warning(f"  - {warning}")

    # Create and show the main window
    window = MainWindow(
        media_csv_path=args.media_csv,
        categories_csv_path=args.categories_csv,
        training_data_dir=args.training_data_dir,
        available_models=available_models,
    )
    window.show()

    # Run the application
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
