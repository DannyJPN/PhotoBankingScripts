"""
Module for analyzing photos and videos using ExifTool.
Contains functions for extracting metadata and validating against limits.
"""
import os
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from updatemedialdatabaselib.constants import (
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    VECTOR_EXTENSIONS,
    TYPE_PHOTO,
    TYPE_VIDEO,
    TYPE_VECTOR,
    TYPE_EDITED_PHOTO,
    TYPE_EDITED_VIDEO,
    LIMITS_COLUMN_BANK,
    LIMITS_COLUMN_WIDTH,
    LIMITS_COLUMN_HEIGHT,
    LIMITS_COLUMN_RESOLUTION,
    LIMITS_COLUMN_MEDIA_TYPE,
    TYPE_EDITED_VECTOR
)

def extract_metadata(file_path: str, exiftool_path: str) -> Dict[str, Any]:
    """
    Extract metadata from a media file using ExifTool.
    
    Args:
        file_path: Path to the media file
        exiftool_path: Path to the ExifTool executable
        
    Returns:
        Dictionary of metadata
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return {}
        
    if not os.path.exists(exiftool_path):
        logging.error(f"ExifTool not found: {exiftool_path}")
        return {}
    
    try:
        # Normalize file path for ExifTool (use forward slashes)
        normalized_path = file_path.replace('\\', '/')
        
        # Run ExifTool to extract metadata in JSON format
        command = [
            exiftool_path,
            "-j",  # JSON output format
            "-charset", "utf8", 
            "-n",  # Numeric values (no conversion)
            normalized_path
        ]
        
        logging.debug(f"Running ExifTool command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)

        # Check if we have valid output
        if not result.stdout:
            logging.warning(f"No stdout from ExifTool for: {file_path}")
            return {}

        # Parse JSON output
        metadata_list = json.loads(result.stdout)
        if not metadata_list:
            logging.warning(f"No metadata extracted from: {file_path}")
            return {}
            
        # ExifTool returns a list with one item per file
        raw_metadata = metadata_list[0]
        
        # Check for ExifTool errors - if corrupted, return minimal data
        if "Error" in raw_metadata:
            logging.debug(f"Corrupted file {file_path}: {raw_metadata['Error']}")
            return {}
        
        # Extract relevant metadata
        metadata = {
            "Filename": os.path.basename(file_path),
            "Path": file_path,  # Store full path for category extraction
            "Size": os.path.getsize(file_path),
        }
        
        # Determine file type
        ext = os.path.splitext(file_path)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            metadata["Type"] = TYPE_PHOTO
        elif ext in VIDEO_EXTENSIONS:
            metadata["Type"] = TYPE_VIDEO
        elif ext in VECTOR_EXTENSIONS:
            metadata["Type"] = TYPE_VECTOR
        else:
            metadata["Type"] = "Unknown"
        
        # Extract dimensions (different fields for photos vs videos)
        width_fields = ["ImageWidth", "SourceImageWidth", "VideoFrameWidth", "Width"]
        height_fields = ["ImageHeight", "SourceImageHeight", "VideoFrameHeight", "Height"]
        
        for width_field in width_fields:
            if width_field in raw_metadata and raw_metadata[width_field]:
                metadata["Width"] = int(raw_metadata[width_field])
                break
        
        for height_field in height_fields:
            if height_field in raw_metadata and raw_metadata[height_field]:
                metadata["Height"] = int(raw_metadata[height_field])
                break
        
        # Extract date
        date_fields = ["DateTimeOriginal", "CreateDate", "ModifyDate"]
        for field in date_fields:
            if field in raw_metadata:
                date_str = raw_metadata[field]
                try:
                    # Parse date in format "YYYY:MM:DD HH:MM:SS"
                    date_obj = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    metadata["Date"] = date_obj.strftime("%d.%m.%Y")  # Format as DD.MM.YYYY
                    break
                except ValueError:
                    logging.warning(f"Could not parse date '{date_str}' from field '{field}'")
        
        # If no date found, use file modification time
        if "Date" not in metadata:
            metadata["Date"] = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%d.%m.%Y")
        
        # Extract title and description
        if "Title" in raw_metadata:
            metadata["Title"] = raw_metadata["Title"]
        if "Description" in raw_metadata or "ImageDescription" in raw_metadata:
            metadata["Description"] = raw_metadata.get("Description", raw_metadata.get("ImageDescription", ""))
        
        # Extract keywords
        if "Keywords" in raw_metadata:
            keywords = raw_metadata["Keywords"]
            if isinstance(keywords, list):
                metadata["Keywords"] = ", ".join(keywords)
            else:
                metadata["Keywords"] = keywords
        
        # Extract camera info
        if "Model" in raw_metadata:
            metadata["Camera"] = raw_metadata["Model"]

        # Extract resolution in Mpx - try to find existing resolution field or calculate from dimensions
        resolution_mpx = None

        # First, try to find existing resolution fields that might contain Mpx values
        resolution_fields = ["MegaPixels", "Resolution", "EffectivePixels"]
        for field in resolution_fields:
            if field in raw_metadata and raw_metadata[field]:
                try:
                    # Try to parse as number (might already be in Mpx)
                    res_value = float(raw_metadata[field])
                    if res_value > 0:
                        resolution_mpx = res_value
                        break
                except (ValueError, TypeError):
                    continue

        # If no resolution found but we have dimensions, calculate it
        if resolution_mpx is None and "Width" in metadata and "Height" in metadata:
            width = metadata["Width"]
            height = metadata["Height"]
            if width and height:
                resolution_mpx = (width * height) / 1_000_000

        # Store resolution in Mpx format if found/calculated
        if resolution_mpx is not None:
            metadata["Resolution"] = f"{resolution_mpx:.1f}"

        # Extract duration for videos
        if metadata["Type"] in [TYPE_VIDEO, TYPE_EDITED_VIDEO]:
            duration_fields = ["Duration", "MovieDuration", "MediaDuration", "TrackDuration"]
            for field in duration_fields:
                if field in raw_metadata and raw_metadata[field]:
                    metadata["Duration"] = str(raw_metadata[field])
                    break
        
        logging.debug(f"Extracted metadata from: {file_path}")
        return metadata
    
    except subprocess.CalledProcessError as e:
        logging.warning(f"ExifTool failed for {file_path}: {e.stderr.strip() if e.stderr else 'Unknown error'}")
        logging.debug(f"ExifTool command: {' '.join(command)}")
        # Return basic metadata even if ExifTool fails
        ext = os.path.splitext(file_path)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            fallback_type = TYPE_PHOTO
        elif ext in VIDEO_EXTENSIONS:
            fallback_type = TYPE_VIDEO
        elif ext in VECTOR_EXTENSIONS:
            fallback_type = TYPE_VECTOR
        else:
            fallback_type = "Unknown"
        return {
            "Filename": os.path.basename(file_path),
            "Path": file_path,
            "Size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "Type": fallback_type,
            "Date": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%d.%m.%Y") if os.path.exists(file_path) else ""
        }
    except Exception as e:
        logging.error(f"Error extracting metadata from {file_path}: {e}")
        return {
            "Filename": os.path.basename(file_path),
            "Path": file_path,
            "Size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "Type": "Unknown"
        }

def normalize_media_type(media_type: str) -> str:
    """
    Normalize edited media types to their base type.

    Args:
        media_type: Media type string from metadata

    Returns:
        Base media type for limit matching
    """
    if media_type == TYPE_EDITED_PHOTO:
        return TYPE_PHOTO
    if media_type == TYPE_EDITED_VIDEO:
        return TYPE_VIDEO
    if media_type == TYPE_EDITED_VECTOR:
        return TYPE_VECTOR
    return media_type


def validate_against_limits(metadata: Dict[str, Any], limits: List[Dict[str, str]]) -> Dict[str, bool]:
    """
    Validate media metadata against limits for different photo banks.
    
    Args:
        metadata: Media metadata
        limits: List of dictionaries with limits for each photo bank
        
    Returns:
        Dictionary mapping photo bank names to boolean validation results
    """
    results = {}

    media_type = normalize_media_type(metadata.get("Type", ""))
    if not media_type:
        for limit in limits:
            bank_name = limit.get(LIMITS_COLUMN_BANK, "Unknown")
            results[bank_name] = True
        return results

    # If no dimensions available, assume file meets all limits
    if "Width" not in metadata or "Height" not in metadata:
        logging.debug(f"No dimensions available for {metadata.get('Filename', 'unknown file')}: assuming all limits met")
        for limit in limits:
            bank_name = limit.get(LIMITS_COLUMN_BANK, "Unknown")
            results[bank_name] = True
        return results
    
    width = int(metadata["Width"])
    height = int(metadata["Height"])
    size_bytes = int(metadata.get("Size", 0))
    size_mb = size_bytes / (1024 * 1024)  # Convert to MB
    
    limits_by_bank: Dict[str, List[Dict[str, str]]] = {}
    for limit in limits:
        bank_name = limit.get(LIMITS_COLUMN_BANK, "Unknown")
        limits_by_bank.setdefault(bank_name, []).append(limit)

    for bank_name, bank_limits in limits_by_bank.items():
        matching_limits = []
        for limit in bank_limits:
            limit_type = limit.get(LIMITS_COLUMN_MEDIA_TYPE, "").strip()
            if not limit_type:
                limit_type = TYPE_PHOTO
            if limit_type != media_type:
                continue
            matching_limits.append(limit)

        if not matching_limits:
            # Bank doesn't support this media type
            results[bank_name] = False
            continue
        
        bank_valid = True
        for limit in matching_limits:
            # Check available fields (using actual CSV column names)
            required_fields = [LIMITS_COLUMN_WIDTH, LIMITS_COLUMN_HEIGHT, LIMITS_COLUMN_RESOLUTION]
            missing_fields = [field for field in required_fields if field not in limit]
            if missing_fields:
                available_fields = list(limit.keys())
                logging.warning(
                    f"PHOTOBANK '{bank_name}': Missing required limit fields {missing_fields}. "
                    f"Available fields: {available_fields}. Skipping validation for this bank."
                )
                continue
            
            # Convert limits to integers/floats
            try:
                min_width = int(limit[LIMITS_COLUMN_WIDTH]) if limit[LIMITS_COLUMN_WIDTH] != '0' else 0
                min_height = int(limit[LIMITS_COLUMN_HEIGHT]) if limit[LIMITS_COLUMN_HEIGHT] != '0' else 0
                min_resolution_mp = float(limit[LIMITS_COLUMN_RESOLUTION])
            except (ValueError, TypeError):
                invalid_values = {}
                for field in [LIMITS_COLUMN_WIDTH, LIMITS_COLUMN_HEIGHT, LIMITS_COLUMN_RESOLUTION]:
                    try:
                        if field == LIMITS_COLUMN_RESOLUTION:
                            float(limit[field])
                        else:
                            int(limit[field])
                    except (ValueError, TypeError):
                        invalid_values[field] = limit.get(field, 'missing')
                
                logging.warning(
                    f"PHOTOBANK '{bank_name}': Invalid limit values {invalid_values} - expected numeric values. "
                    "Skipping validation for this bank."
                )
                continue
            
            # Calculate actual resolution in megapixels
            actual_resolution_mp = (width * height) / 1_000_000
            
            # Validate dimensions and resolution
            width_ok = (min_width == 0) or (width >= min_width)
            height_ok = (min_height == 0) or (height >= min_height)
            resolution_ok = actual_resolution_mp >= min_resolution_mp
            
            # Log validation details
            if not (width_ok and height_ok and resolution_ok):
                issues = []
                if not width_ok:
                    issues.append(f"width {width}px < minimum {min_width}px")
                if not height_ok:
                    issues.append(f"height {height}px < minimum {min_height}px")
                if not resolution_ok:
                    issues.append(f"resolution {actual_resolution_mp:.2f}MP < minimum {min_resolution_mp}MP")
                
                logging.debug(f"File {metadata.get('Filename', 'unknown')} invalid for {bank_name}: {', '.join(issues)}")
                bank_valid = False
                break

        results[bank_name] = bank_valid
    
    return results
