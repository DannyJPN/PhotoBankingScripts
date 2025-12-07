"""
Integrate sorted photos script.

This script copies files from a sorted folder to a target folder, preserving
file metadata and directory structure. It uses memory-efficient streaming
to handle large directory trees.
"""

import os
import sys
import logging
import argparse
from shared.logging_config import setup_logging
from integratesortedphotoslib.constants import (
    DEFAULT_SORTED_FOLDER,
    DEFAULT_TARGET_FOLDER,
    DEFAULT_LOG_DIR,
    DEFAULT_COPY_METHOD,
    DEFAULT_OVERWRITE,
    BATCH_SIZE_LIMIT,
    SAMPLE_SIZE,
)
from integratesortedphotoslib.copy_files import (
    copy_files_with_preserved_dates,
    copy_files_streaming,
    copy_files_with_progress_estimation,
    estimate_file_count,
)
from shared.utils import get_log_filename
from shared.file_operations import ensure_directory


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Integrate sorted photos from one directory to another with memory-efficient copying."
    )

    # Directory arguments
    parser.add_argument(
        "--sortedFolder",
        type=str,
        nargs="?",
        default=DEFAULT_SORTED_FOLDER,
        help="Path to the sorted folder (source)",
    )
    parser.add_argument(
        "--targetFolder",
        type=str,
        nargs="?",
        default=DEFAULT_TARGET_FOLDER,
        help="Path to the target folder (destination)",
    )
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR, help="Directory for log files")

    # Copy method arguments
    parser.add_argument(
        "--copy-method",
        choices=["streaming", "batch", "estimated"],
        default=DEFAULT_COPY_METHOD,
        help="Copy method: streaming (minimal memory), batch (legacy, uses more memory), or estimated (streaming with progress estimation)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=DEFAULT_OVERWRITE,
        help="Overwrite existing destination files",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=SAMPLE_SIZE,
        help="Number of directories to sample for file count estimation (used with --copy-method=estimated)",
    )

    # Logging arguments
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    return parser.parse_args()


def main():
    """
    Main entry point for the integrate sorted photos script.

    This function orchestrates the entire copy operation, including:
    - Parsing command-line arguments
    - Setting up logging
    - Validating paths
    - Choosing and executing the appropriate copy method
    """
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    logging.info("=" * 80)
    logging.info("Starting integrate sorted photos")
    logging.info("=" * 80)
    logging.info(f"Source folder: {args.sortedFolder}")
    logging.info(f"Target folder: {args.targetFolder}")
    logging.info(f"Copy method: {args.copy_method}")
    logging.info(f"Overwrite mode: {args.overwrite}")
    logging.info(f"Debug mode: {args.debug}")

    # Ensure the source path is valid
    if not os.path.exists(args.sortedFolder):
        logging.error(f"Source folder does not exist: {args.sortedFolder}")
        sys.exit(1)

    if not os.path.isdir(args.sortedFolder):
        logging.error(f"Source path is not a directory: {args.sortedFolder}")
        sys.exit(1)

    # Validate source and destination paths to prevent dangerous operations
    src_abs = os.path.abspath(args.sortedFolder)
    dest_abs = os.path.abspath(args.targetFolder)

    if src_abs == dest_abs:
        logging.error("Source and destination cannot be the same directory")
        sys.exit(1)

    if dest_abs.startswith(src_abs + os.sep):
        logging.error("Destination cannot be inside source directory (would cause infinite loop)")
        sys.exit(1)

    if src_abs.startswith(dest_abs + os.sep):
        logging.error("Source cannot be inside destination directory (would cause data loss)")
        sys.exit(1)

    # Choose copy method based on arguments
    try:
        if args.copy_method == "streaming":
            logging.info("Using streaming copy method (minimal memory usage)")
            copy_files_streaming(args.sortedFolder, args.targetFolder, args.overwrite)

        elif args.copy_method == "estimated":
            logging.info("Using estimated progress copy method (minimal memory with progress %)")
            copy_files_with_progress_estimation(args.sortedFolder, args.targetFolder, args.overwrite, args.sample_size)

        elif args.copy_method == "batch":
            # Legacy batch method with memory check
            logging.info("Using batch copy method (legacy mode)")
            logging.info("Estimating file count to check if streaming should be used instead...")

            estimated_count = estimate_file_count(args.sortedFolder, sample_size=50)

            if estimated_count > BATCH_SIZE_LIMIT:
                logging.warning(
                    f"Large file set detected ({estimated_count} estimated files, limit: {BATCH_SIZE_LIMIT})"
                )
                logging.warning("Automatically switching to streaming method to prevent memory issues")
                copy_files_streaming(args.sortedFolder, args.targetFolder, args.overwrite)
            else:
                logging.info(f"File count ({estimated_count}) is within batch limit, proceeding with batch method")
                copy_files_with_preserved_dates(args.sortedFolder, args.targetFolder, overwrite=args.overwrite)

        logging.info("=" * 80)
        logging.info("Integration completed successfully")
        logging.info("=" * 80)

    except Exception as e:
        logging.error("=" * 80)
        logging.error(f"Integration failed: {e}")
        logging.error("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
