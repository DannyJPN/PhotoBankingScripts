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
from givephotobankreadymediafileslib.media_viewer import show_media_viewer
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
        
        # Load existing media record if CSV provided
        record = None
        if args.media_csv and os.path.exists(args.media_csv):
            logging.info(f"Loading existing records from: {args.media_csv}")
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
                            logging.info(f"Found existing record for file: {os.path.basename(args.file)}")
                            break
                
                if not record:
                    logging.info(f"No existing record found for: {os.path.basename(args.file)}")
                    
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
                # Editorial is not saved - will be detected later by another script
                # Category columns will be added dynamically when needed
            }
            logging.info(f"Created new record for: {os.path.basename(args.file)}")
        
        def metadata_callback(metadata):
            """Handle metadata save from GUI - save to CSV file."""
            logging.info(f"Metadata saved for {args.file}: {metadata}")
            
            try:
                # Load current CSV data
                if args.media_csv and os.path.exists(args.media_csv):
                    from shared.file_operations import load_csv, save_csv_with_backup
                    records = load_csv(args.media_csv)
                    logging.info(f"Loaded {len(records)} existing records from CSV")
                    
                    # Find record for current file
                    file_basename = os.path.basename(args.file)
                    record_updated = False
                    
                    # Import constants for column names and status values
                    from givephotobankreadymediafileslib.constants import (COL_FILE, COL_TITLE, COL_DESCRIPTION,
                                                                           COL_KEYWORDS, COL_PREP_DATE,
                                                                           get_status_column, get_category_column,
                                                                           COL_STATUS_SUFFIX, STATUS_UNPROCESSED,
                                                                           STATUS_PREPARED, STATUS_REJECTED,
                                                                           MAX_TITLE_LENGTH, MAX_DESCRIPTION_LENGTH)
                    from datetime import datetime
                    
                    for record in records:
                        # Match by filename using proper column constant
                        if record.get(COL_FILE, '') == file_basename or record.get('File', '') == file_basename:
                            # Check if this is a rejection
                            is_rejected = metadata.get('rejected', False)
                            
                            if is_rejected:
                                # Handle rejection - set all statuses to rejected
                                logging.info(f"Rejecting file: {file_basename}")
                                record[COL_PREP_DATE] = datetime.now().strftime('%d.%m.%Y')
                                
                                # Set status to rejected for all photobanks
                                for field_name, field_value in record.items():
                                    if field_name.endswith(COL_STATUS_SUFFIX) and field_value.lower() == STATUS_UNPROCESSED.lower():
                                        photobank = field_name.replace(COL_STATUS_SUFFIX, '')
                                        record[field_name] = STATUS_REJECTED
                                        logging.info(f"Rejected status for {photobank}: {STATUS_UNPROCESSED} -> {STATUS_REJECTED}")
                            else:
                                # Handle normal save - update metadata and set status to prepared
                                record[COL_TITLE] = metadata['title'][:MAX_TITLE_LENGTH]
                                record[COL_DESCRIPTION] = metadata['description'][:MAX_DESCRIPTION_LENGTH]
                                record[COL_KEYWORDS] = metadata['keywords']
                                
                                # Set preparation date
                                record[COL_PREP_DATE] = datetime.now().strftime('%d.%m.%Y')
                                
                                # Update categories for each photobank using dynamic column names
                                categories_data = metadata.get('categories', {})
                                for photobank, selected_categories in categories_data.items():
                                    if selected_categories:  # Only if categories were selected
                                        category_column = get_category_column(photobank)
                                        # Join categories with comma
                                        record[category_column] = ', '.join(selected_categories)
                                        logging.info(f"Set categories for {photobank}: {record[category_column]}")
                                
                                # Update status from STATUS_UNPROCESSED to STATUS_PREPARED for ALL photobanks (independent of categories)
                                for field_name, field_value in record.items():
                                    if field_name.endswith(COL_STATUS_SUFFIX) and field_value.lower() == STATUS_UNPROCESSED.lower():
                                        photobank = field_name.replace(COL_STATUS_SUFFIX, '')
                                        record[field_name] = STATUS_PREPARED
                                        logging.info(f"Updated status for {photobank}: {STATUS_UNPROCESSED} -> {STATUS_PREPARED}")
                            
                            # Editorial is not saved - will be detected later by another script from description
                            
                            record_updated = True
                            logging.info(f"Updated record for {file_basename}")
                            break
                    
                    if record_updated:
                        # Generate alternative versions if not rejected
                        if not metadata.get('rejected', False):
                            try:
                                from givephotobankreadymediafileslib.alternative_generator import AlternativeGenerator, get_alternative_output_dirs
                                from givephotobankreadymediafileslib.constants import (ORIGINAL_NO, COL_PATH, COL_FILE, COL_TITLE,
                                                                                       COL_DESCRIPTION, COL_KEYWORDS, COL_ORIGINAL,
                                                                                       CSV_ALLOWED_EXTENSIONS, COL_STATUS_SUFFIX,
                                                                                       STATUS_BACKUP)

                                # Parse keywords if string
                                keywords = metadata.get('keywords', '')
                                if isinstance(keywords, str):
                                    keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]

                                # Generate alternative image files
                                generator = AlternativeGenerator()
                                target_dir, edited_dir = get_alternative_output_dirs(args.file)

                                logging.info(f"Generating alternative versions for {args.file}")
                                print("Generating alternative versions...")

                                alternative_files = generator.generate_all_versions(args.file, target_dir, edited_dir)

                                # Get alternative metadata from metadata dict (already generated by AI in media_viewer)
                                alternative_metadata = metadata.get('alternative_metadata', {})

                                for alt_info in alternative_files:
                                    # Add AI metadata for edit alternatives if available
                                    if alt_info['type'] == 'edit' and alternative_metadata:
                                        edit_tag = alt_info['edit']

                                        # Check if we have AI-generated metadata for this edit type
                                        if edit_tag in alternative_metadata:
                                            alt_meta = alternative_metadata[edit_tag]

                                            # Store AI-generated metadata in alt_info
                                            if 'title' in alt_meta:
                                                alt_info['title'] = alt_meta['title']
                                            if 'description' in alt_meta:
                                                alt_info['alt_description'] = alt_meta['description']
                                            if 'keywords' in alt_meta:
                                                alt_info['keywords'] = alt_meta['keywords']

                                            logging.info(f"Using AI-generated metadata for {edit_tag}: {alt_meta.get('title', '')[:50]}...")
                                        else:
                                            logging.warning(f"No AI-generated metadata found for {edit_tag} alternative")

                                # Add/update alternative files in CSV records (only JPG, video, vector formats)
                                for alt_info in alternative_files:
                                    file_ext = os.path.splitext(alt_info['path'])[1].lower()

                                    # Only add allowed formats to CSV (not PNG/TIF)
                                    if file_ext not in CSV_ALLOWED_EXTENSIONS:
                                        logging.info(f"Skipping CSV entry for {file_ext} file: {os.path.basename(alt_info['path'])}")
                                        continue

                                    alt_filename = os.path.basename(alt_info['path'])

                                    # Check if record already exists
                                    existing_index = None
                                    for idx, existing_record in enumerate(records):
                                        if existing_record.get(COL_FILE) == alt_filename:
                                            existing_index = idx
                                            break

                                    # Create or update record
                                    if existing_index is not None:
                                        # Update existing record
                                        alt_record = records[existing_index]
                                        logging.info(f"Updating existing alternative record: {alt_filename}")
                                    else:
                                        # Create new record from original
                                        alt_record = record.copy()
                                        logging.info(f"Creating new alternative record: {alt_filename}")

                                    # Update file-specific fields
                                    alt_record[COL_FILE] = alt_filename
                                    alt_record[COL_PATH] = alt_info['path']
                                    alt_record[COL_ORIGINAL] = ORIGINAL_NO  # Alternatives are not originals

                                    # Set status to "záložní" for _sharpen files (backup alternative)
                                    # Other alternatives keep "připraveno" status from original
                                    if alt_info.get('edit') == '_sharpen':
                                        for field_name in alt_record.keys():
                                            if field_name.endswith(COL_STATUS_SUFFIX):
                                                alt_record[field_name] = STATUS_BACKUP
                                        logging.info(f"Set _sharpen status to 'záložní': {alt_filename}")

                                    # Use AI-generated metadata if available, otherwise add edit tag to title
                                    if alt_info['type'] == 'edit' and 'title' in alt_info:
                                        # Use AI-adjusted metadata
                                        alt_record[COL_TITLE] = alt_info['title'][:MAX_TITLE_LENGTH]
                                        if 'alt_description' in alt_info:
                                            alt_record[COL_DESCRIPTION] = alt_info['alt_description'][:MAX_DESCRIPTION_LENGTH]
                                        if 'keywords' in alt_info:
                                            alt_record[COL_KEYWORDS] = ', '.join(alt_info['keywords'][:50])
                                        logging.info(f"Using AI-adjusted metadata for {alt_record[COL_FILE]}")
                                    elif alt_info['type'] == 'edit':
                                        # Fallback: add edit tag to title
                                        edit_suffix = f" ({alt_info['description']})"
                                        if not alt_record[COL_TITLE].endswith(edit_suffix):
                                            alt_record[COL_TITLE] = (alt_record[COL_TITLE] + edit_suffix)[:MAX_TITLE_LENGTH]

                                    # Add only if new (existing ones are already updated in-place)
                                    if existing_index is None:
                                        records.append(alt_record)

                                logging.info(f"Generated {len(alternative_files)} alternative versions")
                                print(f"Generated {len(alternative_files)} alternative versions")

                            except Exception as e:
                                logging.error(f"Failed to generate alternative versions: {e}")
                                print(f"Warning: Failed to generate alternatives: {e}")

                        # Save updated CSV with backup (including alternatives)
                        save_csv_with_backup(records, args.media_csv)
                        logging.info(f"Successfully saved metadata to CSV: {args.media_csv}")
                        print(f"✅ Metadata saved to CSV: {metadata['title']}")
                    else:
                        logging.warning(f"No matching record found for {file_basename} in CSV")
                        print(f"⚠️ Warning: No record found for {file_basename} in CSV")
                        
                else:
                    logging.warning("No CSV file specified or file doesn't exist - metadata not saved to file")
                    print(f"⚠️ Warning: No CSV file - metadata only logged: {metadata['title']}")
                    
            except Exception as e:
                logging.error(f"Failed to save metadata to CSV: {e}")
                print(f"❌ Error saving metadata: {e}")
                
            # Always log the metadata for debugging
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