import os
import logging
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Optional, Union

from shared.exif_downloader import ensure_exiftool

def extract_exif_dates(file_path: str, tool_path: str = None) -> List[datetime]:
    """
    Extracts all available date information from a file's EXIF metadata.

    Args:
        file_path: Path to the file to extract dates from
        tool_path: Path to the ExifTool executable. If None, will be automatically located.

    Returns:
        List of datetime objects representing all available dates found in the file
    """
    # Ensure ExifTool is available
    if tool_path is None:
        tool_path = ensure_exiftool()

    # Define the date tags we're interested in
    date_tags = [
        "CreateDate",
        "DateTimeOriginal",
        "FileModifyDate",
        "FileCreateDate",
        "ModifyDate",
        "MediaCreateDate",
        "MediaModifyDate",
        "TrackCreateDate",
        "TrackModifyDate"
    ]

    # Build the command to extract these specific tags in JSON format
    cmd = [tool_path, "-j", "-time:all", file_path]

    try:
        # Run ExifTool and capture the output
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse the JSON output
        exif_data = json.loads(result.stdout)
        if not exif_data:
            logging.warning(f"No EXIF data found for {file_path}")
            return []

        # Extract all date values
        dates = []
        for tag in date_tags:
            if tag in exif_data[0]:
                date_str = exif_data[0][tag]
                try:
                    # Handle different date formats
                    if ":" in date_str:
                        # Standard EXIF date format: YYYY:MM:DD HH:MM:SS
                        if len(date_str) >= 19:  # Full datetime format
                            dt = datetime.strptime(date_str[:19], "%Y:%m:%d %H:%M:%S")
                            dates.append(dt)
                        elif len(date_str) >= 10:  # Date only format
                            dt = datetime.strptime(date_str[:10], "%Y:%m:%d")
                            dates.append(dt)
                    else:
                        # Try other common formats
                        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%d.%m.%Y %H:%M:%S"]:
                            try:
                                dt = datetime.strptime(date_str, fmt)
                                dates.append(dt)
                                break
                            except ValueError:
                                continue
                except ValueError as e:
                    logging.warning(f"Could not parse date '{date_str}' from tag {tag}: {e}")

        return dates

    except subprocess.CalledProcessError as e:
        logging.error(f"Error running ExifTool on {file_path}: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing ExifTool output for {file_path}: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error processing EXIF data for {file_path}: {e}")
        return []

def update_exif_metadata(file_path: str, metadata: Dict[str, str], tool_path: str = None) -> None:
    """
    Updates the EXIF metadata of a file.

    Args:
        file_path: Path to the file to update
        metadata: Dictionary of tag-value pairs to update
        tool_path: Path to the ExifTool executable. If None, will be automatically located.
    """
    # Ensure ExifTool is available
    if tool_path is None:
        tool_path = ensure_exiftool()

    # Build the command with all metadata tags
    cmd = [tool_path]
    for tag, value in metadata.items():
        cmd.extend([f"-{tag}={value}"])
    cmd.append(file_path)

    try:
        # Run ExifTool to update the metadata
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logging.info(f"Updated EXIF metadata for {file_path}")

    except subprocess.CalledProcessError as e:
        logging.error(f"Error updating EXIF metadata for {file_path}: {e}")
        logging.error(f"ExifTool stderr: {e.stderr}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error updating EXIF metadata for {file_path}: {e}")
        raise

def get_best_creation_date(file_path: str, tool_path: str = None) -> Optional[datetime]:
    """
    Determines the most relevant creation date for a media file.
    Prioritizes EXIF dates over file system dates.

    Args:
        file_path: Path to the file
        tool_path: Path to the ExifTool executable. If None, will be automatically located.

    Returns:
        The most relevant datetime or None if no date could be determined
    """
    # Try to get dates from EXIF metadata
    dates = extract_exif_dates(file_path, tool_path)

    if dates:
        # Sort dates (oldest first) and prioritize them
        dates.sort()
        return dates[0]

    # Fallback to file system dates if no EXIF dates are available
    try:
        # Get file creation time (Windows) or metadata change time (Unix)
        ctime = os.path.getctime(file_path)
        # Get file modification time
        mtime = os.path.getmtime(file_path)

        # Use the earlier of the two times
        return datetime.fromtimestamp(min(ctime, mtime))
    except Exception as e:
        logging.error(f"Error getting file system dates for {file_path}: {e}")
        return None