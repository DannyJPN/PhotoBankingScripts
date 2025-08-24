#!/usr/bin/env python
"""
Give Photobank Ready Media Files - Batch processing tool for preparing media files for photobanks.
"""
import os
import sys
import json
import argparse
import logging
import subprocess
from typing import Dict, Any, List
from datetime import datetime

from PyQt5.QtWidgets import QApplication

from shared.logging_config import setup_logging
from shared.file_operations import ensure_directory, load_csv
from gui.main_window import MainWindow
from givephotobankreadymediafileslib.constants import DEFAULT_LOG_DIR


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Batch process media files for photobanks."
    )
    parser.add_argument("--media_csv", type=str, default="data/PhotoMedia.csv",
                        help="Path to the media CSV file")
    parser.add_argument("--categories_csv", type=str, default="data/PhotoCategories.csv",
                        help="Path to the categories CSV file")
    parser.add_argument("--training_data_dir", type=str, default="data/training",
                        help="Directory for storing training data")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--cli", action="store_true", 
                        help="Run in CLI mode (no GUI)")
    parser.add_argument("--process_next", action="store_true",
                        help="Process the next unprocessed record in CLI mode")
    
    return parser.parse_args()


def process_next_record_cli(media_csv: str, categories_csv: str, training_data_dir: str) -> bool:
    """
    Process the next unprocessed record in CLI mode.
    
    Args:
        media_csv: Path to the media CSV file
        categories_csv: Path to the categories CSV file
        training_data_dir: Directory for storing training data
        
    Returns:
        True if successful, False otherwise
    """
    from core.orchestrator import Orchestrator
    
    # Initialize orchestrator
    orchestrator = Orchestrator(
        media_csv_path=media_csv,
        categories_csv_path=categories_csv,
        training_data_dir=training_data_dir,
        llm_client_type="local"  # Default to local
    )
    
    # Process the next record
    result = orchestrator.process_next_record()
    
    if not result:
        logging.error("Failed to process record")
        return False
    
    # Log success
    logging.info(f"Successfully processed file: {result.get('record', {}).get('Soubor', '')}")
    return True


def run_preparemediafile(file_path: str, record: Dict[str, str], 
                        categories_csv: str, training_data_dir: str) -> Dict[str, Any]:
    """
    Run the preparemediafile.py script for a single file.
    
    Args:
        file_path: Path to the media file
        record: Record dictionary
        categories_csv: Path to the categories CSV file
        training_data_dir: Directory for storing training data
        
    Returns:
        Dictionary with metadata from the script output
    """
    # Convert record to JSON
    record_json = json.dumps(record, ensure_ascii=False)
    
    # Build command
    cmd = [
        sys.executable,
        "preparemediafile.py",
        "--file", file_path,
        "--record", record_json,
        "--categories_file", categories_csv,
        "--training_data_dir", training_data_dir
    ]
    
    # Run the command
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output JSON
        if result.stdout:
            return json.loads(result.stdout)
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running preparemediafile.py: {e}")
        logging.error(f"stderr: {e.stderr}")
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing preparemediafile.py output: {e}")
    
    return {}


def update_record(records: List[Dict[str, str]], record_index: int, 
                 metadata: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Update a record with new metadata.
    
    Args:
        records: List of all records
        record_index: Index of the record to update
        metadata: New metadata
        
    Returns:
        Updated list of records
    """
    if record_index < 0 or record_index >= len(records):
        logging.error(f"Invalid record index: {record_index}")
        return records
    
    # Update the record
    if 'title' in metadata:
        records[record_index]["Název"] = metadata['title']
    
    if 'description' in metadata:
        records[record_index]["Popis"] = metadata['description']
    
    if 'keywords' in metadata:
        records[record_index]["Klíčová slova"] = ", ".join(metadata['keywords'])
    
    # Update categories
    if 'categories' in metadata:
        # Combine all categories into a single string
        all_categories = []
        for bank, categories in metadata['categories'].items():
            if isinstance(categories, str):
                all_categories.append(categories)
            elif isinstance(categories, list):
                all_categories.extend(categories)
        
        # Remove duplicates and join
        unique_categories = list(dict.fromkeys(all_categories))
        records[record_index]["Kategorie"] = ", ".join(unique_categories)
    
    # Update status for all photobanks
    for key in records[record_index]:
        if key.startswith("status_"):
            records[record_index][key] = "zpracováno"
    
    # Update preparation date
    records[record_index]["Datum přípravy"] = datetime.now().strftime("%Y-%m-%d")
    
    return records


def save_records(records: List[Dict[str, str]], media_csv: str) -> bool:
    """
    Save records to the CSV file.
    
    Args:
        records: List of records
        media_csv: Path to the media CSV file
        
    Returns:
        True if successful, False otherwise
    """
    import csv
    
    try:
        # Get the fieldnames from the first record
        if not records:
            logging.warning("No records to save")
            return False
        
        fieldnames = list(records[0].keys())
        
        # Write to CSV
        with open(media_csv, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
            writer.writeheader()
            for record in records:
                writer.writerow(record)
        
        logging.info(f"Saved {len(records)} records to {media_csv}")
        return True
        
    except Exception as e:
        logging.error(f"Error saving records: {e}")
        return False


def main():
    """Main function."""
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
    
    # Check if files exist
    if not os.path.exists(args.media_csv):
        logging.warning(f"Media CSV file not found: {args.media_csv}")
        # Create an empty CSV file
        with open(args.media_csv, 'w', encoding='utf-8-sig', newline='') as f:
            f.write("Soubor,Název,Popis,Datum přípravy,Šířka,Výška,Rozlišení,Klíčová slova,Kategorie,Datum vytvoření,Originál,Cesta,status_Shutterstock,status_Adobe,status_Alamy,status_Dreamstime\n")
        logging.info(f"Created empty media CSV file: {args.media_csv}")
    
    if not os.path.exists(args.categories_csv):
        logging.warning(f"Categories CSV file not found: {args.categories_csv}")
        # Create an empty CSV file
        with open(args.categories_csv, 'w', encoding='utf-8-sig', newline='') as f:
            f.write("Shutterstock,Adobe,Alamy,Dreamstime\n")
        logging.info(f"Created empty categories CSV file: {args.categories_csv}")
    
    # Run in CLI mode if requested
    if args.cli:
        if args.process_next:
            success = process_next_record_cli(
                args.media_csv,
                args.categories_csv,
                args.training_data_dir
            )
            return 0 if success else 1
        else:
            logging.error("No CLI action specified")
            return 1
    
    # Start the GUI application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MainWindow(
        media_csv_path=args.media_csv,
        categories_csv_path=args.categories_csv,
        training_data_dir=args.training_data_dir
    )
    window.show()
    
    # Run the application
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
