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
from givephotobankreadymediafileslib.constants import DEFAULT_LOG_DIR, DEFAULT_CATEGORIES_CSV_PATH, DEFAULT_MEDIA_CSV_PATH
from givephotobankreadymediafileslib.media_viewer_refactored import show_media_viewer
from givephotobankreadymediafileslib.mediainfo_loader import load_categories, load_media_records


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Prepare media file for photobanks."
    )
    parser.add_argument("file", type=str, help="Path to the media file")
    parser.add_argument("--media_csv", type=str, default=DEFAULT_MEDIA_CSV_PATH,
                        help="Path to the PhotoMedia.csv file")
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
    logging.debug("Starting preparemediafile.py")

    # Check if file exists
    if not os.path.exists(args.file):
        logging.error(f"File not found: {args.file}")
        return 1

    try:
        # Load categories
        categories = load_categories(args.categories_csv)
        if not categories:
            logging.warning("No categories loaded, continuing without categories")

        # Load existing media record if CSV provided
        record = None
        if args.media_csv and os.path.exists(args.media_csv):
            logging.debug(f"Loading existing records from: {args.media_csv}")
            try:
                media_records = load_media_records(args.media_csv)

                # Find record matching this file
                file_path_normalized = os.path.abspath(args.file).replace('\\', '/')

                for media_record in media_records:
                    record_path = media_record.get('Cesta', '')
                    if record_path:
                        record_path_normalized = os.path.abspath(record_path).replace('\\', '/')
                        if record_path_normalized == file_path_normalized:
                            record = media_record
                            logging.debug(f"Found existing record for file: {os.path.basename(args.file)}")
                            break

                if not record:
                    logging.debug(f"No existing record found for: {os.path.basename(args.file)}")

            except Exception as e:
                logging.warning(f"Failed to load media records: {e}")

        # Create default record if none found using proper constants
        if not record:
            from givephotobankreadymediafileslib.constants import COL_FILE, COL_PATH, COL_TITLE, COL_DESCRIPTION, COL_KEYWORDS
            record = {
                COL_FILE: os.path.basename(args.file),
                COL_PATH: args.file,
                COL_TITLE: '',
                COL_DESCRIPTION: '',
                COL_KEYWORDS: '',
            }
            logging.debug(f"Created new record for: {os.path.basename(args.file)}")

        # Storage for metadata from GUI
        saved_metadata = {}

        def metadata_callback(metadata):
            """Handle metadata save from GUI - save original to CSV immediately, store for alternatives."""
            logging.debug(f"Metadata received from GUI for {args.file}")
            saved_metadata.update(metadata)

            # Import constants for CSV operations
            from shared.file_operations import load_csv, save_csv_with_backup
            from givephotobankreadymediafileslib.constants import (
                COL_FILE, COL_TITLE, COL_DESCRIPTION, COL_KEYWORDS, COL_PREP_DATE,
                COL_STATUS_SUFFIX, COL_PATH, COL_EDITORIAL, COL_ORIGINAL,
                get_category_column,
                STATUS_UNPROCESSED, STATUS_PREPARED, STATUS_REJECTED,
                MAX_TITLE_LENGTH, MAX_DESCRIPTION_LENGTH,
                PHOTOBANK_CATEGORY_COUNTS
            )
            from datetime import datetime

            # Save original metadata to CSV immediately (before GUI closes)
            if not args.media_csv or not os.path.exists(args.media_csv):
                logging.error("No CSV file specified or doesn't exist")
                return False

            try:
                records = load_csv(args.media_csv)
                logging.debug(f"Loaded {len(records)} existing records from CSV")

                file_basename = os.path.basename(args.file)

                # Find existing record (create-or-update pattern)
                existing_record = None
                record_index = None

                for idx, record in enumerate(records):
                    if record.get(COL_FILE, '') == file_basename:
                        existing_record = record
                        record_index = idx
                        break

                # Create new record if not found
                if existing_record is None:
                    logging.info(f"Creating new CSV record for {file_basename}")
                    existing_record = {
                        COL_FILE: file_basename,
                        COL_PATH: args.file,
                        COL_TITLE: '',
                        COL_DESCRIPTION: '',
                        COL_KEYWORDS: '',
                        COL_PREP_DATE: '',
                        COL_EDITORIAL: 'ne',
                        COL_ORIGINAL: 'ano',
                    }

                    # Initialize status columns for all photobanks
                    for photobank in PHOTOBANK_CATEGORY_COUNTS.keys():
                        status_col = f"{photobank}{COL_STATUS_SUFFIX}"
                        existing_record[status_col] = STATUS_UNPROCESSED

                        category_col = get_category_column(photobank)
                        existing_record[category_col] = ''

                    # Append to records list
                    records.append(existing_record)
                    record_index = len(records) - 1
                    logging.debug(f"New record created at index {record_index}")

                # Now update the record (whether existing or new)
                record = existing_record

                # Check if rejected
                is_rejected = metadata.get('rejected', False)

                if is_rejected:
                    # Handle rejection
                    logging.info(f"Rejecting file: {file_basename}")
                    record[COL_PREP_DATE] = datetime.now().strftime('%d.%m.%Y')

                    for field_name, field_value in record.items():
                        if field_name.endswith(COL_STATUS_SUFFIX) and field_value.lower() == STATUS_UNPROCESSED.lower():
                            photobank = field_name.replace(COL_STATUS_SUFFIX, '')
                            record[field_name] = STATUS_REJECTED
                            logging.debug(f"Rejected status for {photobank}: {STATUS_UNPROCESSED} -> {STATUS_REJECTED}")
                else:
                    # Handle normal save
                    record[COL_TITLE] = metadata['title'][:MAX_TITLE_LENGTH]
                    record[COL_DESCRIPTION] = metadata['description'][:MAX_DESCRIPTION_LENGTH]
                    record[COL_KEYWORDS] = metadata['keywords']
                    record[COL_PREP_DATE] = datetime.now().strftime('%d.%m.%Y')

                    # Update categories
                    categories_data = metadata.get('categories', {})
                    for photobank, selected_categories in categories_data.items():
                        if selected_categories:
                            category_column = get_category_column(photobank)
                            record[category_column] = ', '.join(selected_categories)
                            logging.debug(f"Set categories for {photobank}: {record[category_column]}")

                    # Update status
                    for field_name, field_value in record.items():
                        if field_name.endswith(COL_STATUS_SUFFIX) and field_value.lower() == STATUS_UNPROCESSED.lower():
                            photobank = field_name.replace(COL_STATUS_SUFFIX, '')
                            record[field_name] = STATUS_PREPARED
                            logging.debug(f"Updated status for {photobank}: {STATUS_UNPROCESSED} -> {STATUS_PREPARED}")

                logging.debug(f"{'Updated' if record_index < len(records) - 1 else 'Created'} record for {file_basename}")

                # Save original metadata to CSV immediately
                save_csv_with_backup(records, args.media_csv)
                logging.info(f"Saved metadata for {file_basename}")
                return True

            except Exception as e:
                logging.error(f"Failed to save original metadata to CSV: {e}")
                return False

        # Show GUI with categories - blocks until window closes
        show_media_viewer(args.file, record, metadata_callback, categories)

        # GUI closed - check if metadata was saved
        if not saved_metadata:
            logging.debug("No metadata saved - user closed window without saving")
            return 0

        logging.debug("GUI closed, processing alternatives")

        # Generate alternatives AFTER GUI close (if not rejected)
        if not saved_metadata.get('rejected', False):
            logging.info("Generating alternative versions...")

            try:
                from givephotobankreadymediafileslib.alternative_generator import AlternativeGenerator, get_alternative_output_dirs
                from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator
                from shared.config import get_config
                from tqdm import tqdm

                # Parse keywords
                keywords = saved_metadata.get('keywords', '')
                if isinstance(keywords, str):
                    keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]

                # Parse default alternatives from constants
                from givephotobankreadymediafileslib.constants import DEFAULT_ALTERNATIVE_EFFECTS, EFFECT_NAME_MAPPING
                default_effects = [EFFECT_NAME_MAPPING.get(e.strip().lower(), e.strip())
                                 for e in DEFAULT_ALTERNATIVE_EFFECTS.split(',') if e.strip()]

                # Generate physical alternative files with default effects only
                generator = AlternativeGenerator(enabled_alternatives=default_effects)
                target_dir, edited_dir = get_alternative_output_dirs(args.file)

                logging.info("Creating physical alternative files...")
                alternative_files = generator.generate_all_versions(args.file, target_dir, edited_dir)
                logging.info(f"Created {len(alternative_files)} physical alternative files")

                # Get AI generator for metadata
                selected_model_display = saved_metadata.get('ai_model', '')
                ai_generator = None

                if selected_model_display and selected_model_display not in ["No models available", "Error loading models"]:
                    config = get_config()
                    available_models = config.get_available_ai_models()

                    model_key = None
                    for model in available_models:
                        if model["display_name"] == selected_model_display:
                            model_key = model["key"]
                            break

                    if model_key:
                        logging.debug(f"Using AI model for alternatives: {model_key} ({selected_model_display})")
                        ai_generator = create_metadata_generator(model_key)
                    else:
                        logging.warning(f"Model key not found for: {selected_model_display}")
                else:
                    logging.warning("No valid AI model selected")

                # Get original metadata
                original_title = saved_metadata['title']
                original_description = saved_metadata['description']
                original_keywords_list = keywords
                is_editorial = saved_metadata.get('editorial', False)

                # Generate metadata ONCE per edit tag (not per file)
                edit_metadata = {}  # Store metadata for each edit tag

                if ai_generator:
                    # Get unique edit tags from alternative files
                    unique_edit_tags = set()
                    for alt_info in alternative_files:
                        if alt_info['type'] == 'edit':
                            unique_edit_tags.add(alt_info['edit'])

                    # Generate metadata for each unique edit tag with progress bar
                    logging.debug(f"Generating AI metadata for {len(unique_edit_tags)} alternative versions...")

                    for edit_tag in tqdm(unique_edit_tags, desc="Generating AI metadata", unit="version"):
                        if edit_tag == '_sharpen':
                            # Use original metadata
                            edit_metadata[edit_tag] = {
                                'title': original_title,
                                'description': original_description,
                                'keywords': original_keywords_list
                            }
                            logging.debug(f"Using original metadata for {edit_tag}")
                        else:
                            # Generate AI metadata
                            try:
                                logging.debug(f"Generating metadata for {edit_tag}")

                                alt_title = ai_generator.generate_title_for_alternative(
                                    args.file, edit_tag, original_title
                                )
                                logging.debug(f"Generated title for {edit_tag}: {alt_title[:50]}...")

                                alt_description = ai_generator.generate_description_for_alternative(
                                    args.file, edit_tag, original_title, original_description,
                                    editorial_data={'is_editorial': is_editorial} if is_editorial else None
                                )
                                logging.debug(f"Generated description for {edit_tag}: {alt_description[:50]}...")

                                alt_keywords = ai_generator.generate_keywords_for_alternative(
                                    args.file, edit_tag, original_title, original_description,
                                    original_keywords_list, count=30, is_editorial=is_editorial
                                )
                                logging.debug(f"Generated {len(alt_keywords)} keywords for {edit_tag}")

                                edit_metadata[edit_tag] = {
                                    'title': alt_title,
                                    'description': alt_description,
                                    'keywords': alt_keywords
                                }

                            except Exception as e:
                                logging.error(f"Failed to generate AI metadata for {edit_tag}: {e}")
                                edit_metadata[edit_tag] = None

                # Apply generated metadata to all alternative files
                for alt_info in alternative_files:
                    if alt_info['type'] == 'edit':
                        edit_tag = alt_info['edit']
                        if edit_tag in edit_metadata and edit_metadata[edit_tag]:
                            alt_info['title'] = edit_metadata[edit_tag]['title']
                            alt_info['alt_description'] = edit_metadata[edit_tag]['description']
                            alt_info['keywords'] = edit_metadata[edit_tag]['keywords']

                # Load CSV again for adding alternatives
                from shared.file_operations import load_csv, save_csv_with_backup
                from givephotobankreadymediafileslib.constants import (
                    COL_FILE, COL_TITLE, COL_DESCRIPTION, COL_KEYWORDS, COL_PATH,
                    COL_ORIGINAL, COL_STATUS_SUFFIX, STATUS_BACKUP,
                    MAX_TITLE_LENGTH, MAX_DESCRIPTION_LENGTH, ORIGINAL_NO, CSV_ALLOWED_EXTENSIONS
                )

                if not args.media_csv or not os.path.exists(args.media_csv):
                    logging.warning("No CSV file for alternatives")
                    return 0

                records = load_csv(args.media_csv)
                logging.debug(f"Loaded {len(records)} records for adding alternatives")

                # Find original record
                file_basename = os.path.basename(args.file)
                original_record = None
                for rec in records:
                    if rec.get(COL_FILE, '') == file_basename:
                        original_record = rec
                        break

                if not original_record:
                    logging.warning(f"Original record not found for {file_basename}")
                    return 0

                # Add alternatives to CSV with progress bar
                logging.info(f"Adding {len(alternative_files)} alternatives to database...")

                for alt_info in tqdm(alternative_files, desc="Adding alternatives to CSV", unit="file"):
                    file_ext = os.path.splitext(alt_info['path'])[1].lower()

                    if file_ext not in CSV_ALLOWED_EXTENSIONS:
                        logging.debug(f"Skipping CSV entry for {file_ext} file")
                        continue

                    alt_filename = os.path.basename(alt_info['path'])

                    # Find existing record
                    existing_index = None
                    for idx, existing_record in enumerate(records):
                        if existing_record.get(COL_FILE) == alt_filename:
                            existing_index = idx
                            break

                    # Create or update
                    if existing_index is not None:
                        alt_record = records[existing_index]
                        logging.debug(f"Updating existing alternative: {alt_filename}")
                    else:
                        alt_record = original_record.copy()
                        logging.debug(f"Creating new alternative: {alt_filename}")

                    # Update fields
                    alt_record[COL_FILE] = alt_filename
                    alt_record[COL_PATH] = alt_info['path']
                    alt_record[COL_ORIGINAL] = ORIGINAL_NO

                    # Set status
                    if alt_info.get('edit') == '_sharpen':
                        for field_name in alt_record.keys():
                            if field_name.endswith(COL_STATUS_SUFFIX):
                                alt_record[field_name] = STATUS_BACKUP
                        logging.debug(f"Set _sharpen status to záložní: {alt_filename}")

                    # Set metadata
                    if alt_info['type'] == 'edit' and 'title' in alt_info:
                        alt_record[COL_TITLE] = alt_info['title'][:MAX_TITLE_LENGTH]
                        if 'alt_description' in alt_info:
                            alt_record[COL_DESCRIPTION] = alt_info['alt_description'][:MAX_DESCRIPTION_LENGTH]
                        if 'keywords' in alt_info:
                            alt_record[COL_KEYWORDS] = ', '.join(alt_info['keywords'][:50])
                        logging.debug(f"Using AI metadata for {alt_filename}")
                    elif alt_info['type'] == 'edit':
                        # Fallback
                        edit_suffix = f" ({alt_info['description']})"
                        if not alt_record[COL_TITLE].endswith(edit_suffix):
                            alt_record[COL_TITLE] = (alt_record[COL_TITLE] + edit_suffix)[:MAX_TITLE_LENGTH]
                        logging.debug(f"Using fallback title for {alt_filename}")

                    # Add if new
                    if existing_index is None:
                        records.append(alt_record)

                # Save final CSV with alternatives
                save_csv_with_backup(records, args.media_csv)
                logging.info(f"Saved {len(alternative_files)} alternatives")

            except Exception as e:
                logging.error(f"Failed to generate alternatives: {e}")

        logging.debug("Application closed successfully")
        return 0

    except Exception as e:
        logging.error(f"Error running application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())