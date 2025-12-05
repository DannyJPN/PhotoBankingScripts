import logging
import os
from typing import Dict, List
from pathlib import Path
from shared.file_operations import ensure_directory, copy_file
from shared.exif_handler import update_exif_metadata
from shared.csv_sanitizer import sanitize_field
from createbatchlib.constants import (
    STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE,
    PHOTOBANK_SUPPORTED_FORMATS, FORMAT_SUBDIRS, ALTERNATIVE_EDIT_TAGS
)

def prepare_media_file(
    record: Dict[str, str],
    output_folder: str,
    exif_tool_path: str,
    overwrite: bool = True,
    bank: str = None,
    include_alternative_formats: bool = False
) -> List[str]:
    """
    Copy a media file into output_folder/<photobank>/<format>/ and update its EXIF metadata.
    If 'bank' is specified, only files for that photobank are processed.
    If include_alternative_formats is True, also copy alternative format versions (PNG, TIFF, RAW).

    Returns a list of paths where the file was copied.
    """
    src = record.get('Cesta')
    if not src or not os.path.exists(src):
        logging.warning(f"Source file does not exist: {src}")
        return []

    processed_paths: List[str] = []

    # Get metadata for EXIF update (sanitize to prevent CSV injection)
    metadata = {
        'title': sanitize_field(record.get('Název', '')),
        'keywords': sanitize_field(record.get('Klíčová slova', '')),
        'description': sanitize_field(record.get('Popis', '')),
        'datetimeoriginal': sanitize_field(record.get('Datum pořízení', ''))
    }

    # Process for each photobank that has PREPARED status
    for key, value in record.items():
        if STATUS_FIELD_KEYWORD in key.lower() \
           and isinstance(value, str) \
           and PREPARED_STATUS_VALUE.lower() in value.lower():
            bank_name = key[:key.lower().find(STATUS_FIELD_KEYWORD)].strip()
            if bank and bank_name != bank:
                continue

            # Get supported formats for this photobank
            supported_formats = PHOTOBANK_SUPPORTED_FORMATS.get(bank_name, {'.jpg'})

            # Find files to copy (base file + alternative formats if enabled)
            files_to_copy = _find_files_to_copy(src, include_alternative_formats, supported_formats)

            # Copy each file to appropriate subdirectory
            for file_path in files_to_copy:
                file_ext = Path(file_path).suffix.lower()
                file_stem = Path(file_path).stem
                filename = os.path.basename(file_path)

                # Get format subdirectory name
                format_subdir = FORMAT_SUBDIRS.get(file_ext, 'other')

                # Detect edit tag in filename
                edit_tag = None
                for tag in ALTERNATIVE_EDIT_TAGS.keys():
                    if file_stem.endswith(tag):
                        edit_tag = tag
                        break

                # Create edit subfolder (original or tag)
                edit_subfolder = edit_tag if edit_tag else 'original'

                # Create destination path: output_folder/BankName/format/edit/filename
                bank_folder = os.path.join(output_folder, bank_name, format_subdir, edit_subfolder)
                ensure_directory(bank_folder)
                dest = os.path.join(bank_folder, filename)

                logging.debug(
                    "Copying %s to %s for bank %s (format: %s, overwrite=%s)",
                    file_path, dest, bank_name, file_ext, overwrite
                )

                try:
                    copy_file(file_path, dest, overwrite=overwrite)
                    update_exif_metadata(dest, metadata, exif_tool_path)
                    processed_paths.append(dest)
                    logging.debug("Prepared media file for %s: %s", bank_name, dest)
                except Exception as e:
                    logging.error(f"Failed to copy/process {file_path} to {dest}: {e}")

    return processed_paths


def _find_files_to_copy(
    source_file: str,
    include_alternatives: bool,
    supported_formats: set
) -> List[str]:
    """
    Find all file versions to copy based on source file and settings.

    Alternative formats are in parallel directory structure:
    J:/Foto/JPG/Category/Year/Month/Device/file.jpg
    J:/Foto/PNG/Category/Year/Month/Device/file.png
    J:/Foto/TIF/Category/Year/Month/Device/file.tif

    Args:
        source_file: Path to the base file (from CSV)
        include_alternatives: Whether to include alternative formats
        supported_formats: Set of supported format extensions for this photobank

    Returns:
        List of file paths to copy
    """
    files = []
    source_path = Path(source_file)
    source_ext = source_path.suffix.lower()

    # Always add the source file if it's in supported formats
    if source_ext in supported_formats:
        files.append(source_file)
    else:
        logging.debug(f"Source file format {source_ext} not supported, skipping: {source_file}")

    # If alternative formats are enabled, search for them in parallel directories
    if include_alternatives:
        # Get all valid format directory names from FORMAT_SUBDIRS
        valid_format_dirs = {subdir.upper() for subdir in FORMAT_SUBDIRS.values()}

        # Find which part of the path is the format directory
        source_parts = source_path.parts
        current_format_dir = None
        format_dir_index = None

        for i, part in enumerate(source_parts):
            if part.upper() in valid_format_dirs:
                current_format_dir = part
                format_dir_index = i
                break

        if current_format_dir is None or format_dir_index is None:
            logging.warning(f"Could not identify format directory in path: {source_file}")
            return files

        # Search for files with same name in parallel format directories
        for ext in supported_formats:
            if ext == source_ext:
                continue  # Already added

            # Get target format directory name
            target_format_dir = FORMAT_SUBDIRS.get(ext, ext.lstrip('.')).upper()

            # Build alternative file path by replacing format directory
            alternative_parts = list(source_parts)
            alternative_parts[format_dir_index] = target_format_dir
            alternative_parts[-1] = source_path.stem + ext

            alternative_file = Path(*alternative_parts)

            if alternative_file.exists():
                files.append(str(alternative_file))
                logging.debug(f"Found alternative format: {alternative_file}")

    return files
