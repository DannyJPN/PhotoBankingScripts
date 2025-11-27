"""
Media processor for finding and processing unprocessed media records.
"""

import os
import logging
from typing import List, Dict
from datetime import datetime
from tqdm import tqdm

from givephotobankreadymediafileslib.constants import (
    COL_FILE, COL_PATH, COL_ORIGINAL, COL_CREATE_DATE,
    COL_STATUS_SUFFIX, STATUS_UNPROCESSED, ORIGINAL_YES
)
from givephotobankreadymediafileslib.media_helper import get_media_type


def find_unprocessed_records(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Find records that need processing (Originál=ano and any status=STATUS_UNPROCESSED).

    Args:
        records: List of all media records

    Returns:
        List of unprocessed records, sorted by media type (images first, then videos),
        then by creation date, then by filename
    """
    logging.info("Filtering unprocessed records")
    
    unprocessed = []
    
    for record in tqdm(records, desc="Filtering records", unit="records"):
        # Check if it's an original
        if record.get(COL_ORIGINAL, "").lower() != ORIGINAL_YES:
            continue
        
        # Check if any photobank status is unprocessed (using SUFFIX)
        has_unprocessed_status = False
        for key, value in record.items():
            if key.endswith(COL_STATUS_SUFFIX) and value == STATUS_UNPROCESSED:
                has_unprocessed_status = True
                break
        
        if has_unprocessed_status:
            # Validate file path exists
            file_path = record.get(COL_PATH, "")
            if file_path and os.path.exists(file_path):
                unprocessed.append(record)
            else:
                logging.warning(f"File not found, skipping: {file_path}")
    
    # Sort by media type (photos first, then videos), then by creation date, then by filename
    def sort_key(record):
        # Get file path and media type
        file_path = record.get(COL_PATH, "")
        media_type = get_media_type(file_path) if file_path else "unknown"

        # Media type priority: images (0) before videos (1), unknown last (2)
        if media_type == "image":
            type_priority = 0
        elif media_type == "video":
            type_priority = 1
        else:
            type_priority = 2

        # Parse creation date
        date_str = record.get(COL_CREATE_DATE, "")
        if not date_str:
            parsed_date = datetime.min
        else:
            try:
                # Format is DD.MM.YYYY or DD.MM.YYYY HH:MM:SS
                if ' ' not in date_str:
                    # No time part, add 00:00:00
                    date_str += " 00:00:00"

                parsed_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
            except ValueError:
                # If parsing fails, use string comparison as fallback
                parsed_date = datetime.min
                logging.warning(f"Could not parse date '{date_str}' for file {record.get(COL_FILE, 'Unknown')}")

        # Return tuple: (type_priority, date, filename)
        # This ensures: all images sorted by date, then all videos sorted by date
        return (type_priority, parsed_date, record.get(COL_FILE, ""))

    unprocessed.sort(key=sort_key)
    
    logging.info(f"Found {len(unprocessed)} unprocessed records")
    return unprocessed