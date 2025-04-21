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
    PHOTO_EXTENSIONS,
    VIDEO_EXTENSIONS,
    TYPE_PHOTO,
    TYPE_VIDEO,
    TYPE_EDITED_PHOTO,
    TYPE_EDITED_VIDEO
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
        # Run ExifTool to extract metadata in JSON format
        command = [
            exiftool_path,
            "-json",
            "-charset", "utf8",
            "-n",  # Numeric values (no conversion)
            file_path
        ]
        
        logging.debug(f"Running ExifTool command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Parse JSON output
        metadata_list = json.loads(result.stdout)
        if not metadata_list:
            logging.warning(f"No metadata extracted from: {file_path}")
            return {}
            
        # ExifTool returns a list with one item per file
        raw_metadata = metadata_list[0]
        
        # Extract relevant metadata
        metadata = {
            "Filename": os.path.basename(file_path),
            "Path": os.path.dirname(file_path),
            "Size": os.path.getsize(file_path),
        }
        
        # Determine file type
        ext = os.path.splitext(file_path)[1].lower()
        if ext in PHOTO_EXTENSIONS:
            metadata["Type"] = TYPE_PHOTO
        elif ext in VIDEO_EXTENSIONS:
            metadata["Type"] = TYPE_VIDEO
        else:
            metadata["Type"] = "Unknown"
        
        # Extract dimensions
        if "ImageWidth" in raw_metadata and "ImageHeight" in raw_metadata:
            metadata["Width"] = raw_metadata["ImageWidth"]
            metadata["Height"] = raw_metadata["ImageHeight"]
        
        # Extract date
        date_fields = ["DateTimeOriginal", "CreateDate", "ModifyDate"]
        for field in date_fields:
            if field in raw_metadata:
                date_str = raw_metadata[field]
                try:
                    # Parse date in format "YYYY:MM:DD HH:MM:SS"
                    date_obj = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    metadata["Date"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                    break
                except ValueError:
                    logging.warning(f"Could not parse date '{date_str}' from field '{field}'")
        
        # If no date found, use file modification time
        if "Date" not in metadata:
            metadata["Date"] = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
        
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
        
        # Extract camera and lens info
        if "Model" in raw_metadata:
            metadata["Camera"] = raw_metadata["Model"]
        if "LensModel" in raw_metadata or "Lens" in raw_metadata:
            metadata["Lens"] = raw_metadata.get("LensModel", raw_metadata.get("Lens", ""))
        
        # Extract shooting parameters
        if "FocalLength" in raw_metadata:
            metadata["FocalLength"] = f"{raw_metadata['FocalLength']}mm"
        if "FNumber" in raw_metadata:
            metadata["Aperture"] = f"f/{raw_metadata['FNumber']}"
        if "ExposureTime" in raw_metadata:
            # Convert to fraction if needed
            exp_time = raw_metadata["ExposureTime"]
            if exp_time < 1:
                denominator = int(1 / exp_time)
                metadata["Shutter"] = f"1/{denominator}s"
            else:
                metadata["Shutter"] = f"{exp_time}s"
        if "ISO" in raw_metadata:
            metadata["ISO"] = str(raw_metadata["ISO"])
        
        logging.info(f"Extracted metadata from: {file_path}")
        return metadata
    
    except subprocess.CalledProcessError as e:
        logging.error(f"ExifTool failed for {file_path}: {e}")
        logging.debug(f"ExifTool stderr: {e.stderr}")
        return {}
    except Exception as e:
        logging.error(f"Error extracting metadata from {file_path}: {e}")
        return {}

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
    
    # Skip validation if no width/height
    if "Width" not in metadata or "Height" not in metadata:
        logging.warning(f"Cannot validate {metadata.get('Filename', 'unknown file')}: missing dimensions")
        return results
    
    width = int(metadata["Width"])
    height = int(metadata["Height"])
    size_bytes = int(metadata.get("Size", 0))
    size_mb = size_bytes / (1024 * 1024)  # Convert to MB
    
    for limit in limits:
        bank_name = limit.get("BankName", "Unknown")
        
        # Skip if no limits defined
        if not all(k in limit for k in ["MinWidth", "MinHeight", "MaxWidth", "MaxHeight", "MaxSizeMB"]):
            logging.warning(f"Skipping validation for {bank_name}: incomplete limits")
            continue
        
        # Convert limits to integers
        try:
            min_width = int(limit["MinWidth"])
            min_height = int(limit["MinHeight"])
            max_width = int(limit["MaxWidth"])
            max_height = int(limit["MaxHeight"])
            max_size_mb = float(limit["MaxSizeMB"])
        except (ValueError, TypeError) as e:
            logging.warning(f"Skipping validation for {bank_name}: invalid limits ({e})")
            continue
        
        # Validate dimensions and size
        width_ok = min_width <= width <= max_width
        height_ok = min_height <= height <= max_height
        size_ok = size_mb <= max_size_mb
        
        # Overall validation result
        valid = width_ok and height_ok and size_ok
        results[bank_name] = valid
        
        # Log validation details
        if not valid:
            issues = []
            if not width_ok:
                issues.append(f"width {width}px not in range {min_width}-{max_width}px")
            if not height_ok:
                issues.append(f"height {height}px not in range {min_height}-{max_height}px")
            if not size_ok:
                issues.append(f"size {size_mb:.2f}MB exceeds {max_size_mb}MB")
            
            logging.debug(f"File {metadata.get('Filename', 'unknown')} invalid for {bank_name}: {', '.join(issues)}")
    
    return results
