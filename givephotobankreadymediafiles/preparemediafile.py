#!/usr/bin/env python
"""
Prepare Media File - Tool for editing metadata of a single media file.
"""
import os
import sys
import argparse
import logging
import tkinter as tk

from shared.logging_config import setup_logging
from shared.file_operations import ensure_directory
from givephotobankreadymediafileslib.constants import DEFAULT_LOG_DIR, DEFAULT_CATEGORIES_CSV_PATH
from givephotobankreadymediafileslib.media_viewer import show_media_viewer
from givephotobankreadymediafileslib.mediainfo_loader import load_categories


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Prepare media file for photobanks."
    )
    parser.add_argument("file", type=str, help="Path to the media file")
    parser.add_argument("--categories_csv", type=str, default=DEFAULT_CATEGORIES_CSV_PATH,
                        help="Path to the categories CSV file")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    return parser.parse_args()


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    ensure_directory(args.log_dir)
    log_file = os.path.join(args.log_dir, "preparemediafile.log")
    setup_logging(debug=args.debug, log_file=log_file)
    
    # Log startup
    logging.info("Starting preparemediafile.py")
    
    # Check if file exists
    if not os.path.exists(args.file):
        logging.error(f"File not found: {args.file}")
        print(f"Error: File not found: {args.file}")
        return 1
    
    try:
        # Load categories
        categories = load_categories(args.categories_csv)
        if not categories:
            logging.warning("No categories loaded, continuing without categories")
        
        # Create record from file path (minimal record for GUI)
        record = {
            'Soubor': os.path.basename(args.file),
            'Cesta': args.file,
            'Název': '',
            'Popis': '',
            'Klíčová slova': ''
        }
        
        def metadata_callback(metadata):
            """Handle metadata save from GUI."""
            logging.info(f"Metadata saved for {args.file}: {metadata}")
            print(f"Metadata saved: {metadata['title']}")
            print(f"Editorial: {metadata.get('editorial', False)}")
            print(f"Categories: {metadata.get('categories', {})}")
        
        # Show GUI with categories
        show_media_viewer(args.file, record, metadata_callback, categories)
        
        logging.info("Application closed successfully")
        return 0
        
    except Exception as e:
        logging.error(f"Error running application: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())