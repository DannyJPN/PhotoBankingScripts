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


def find_unprocessed_records(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Find records that need processing (Originál=ano and any status=nezpracováno).
    
    Args:
        records: List of all media records
        
    Returns:
        List of unprocessed records, sorted by date and filename
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
    
    # Sort by creation date (parsed as datetime) and filename, like PowerShell version
    def sort_key(record):
        date_str = record.get(COL_CREATE_DATE, "")
        if not date_str:
            return (datetime.min, record.get(COL_FILE, ""))
        
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
        
        return (parsed_date, record.get(COL_FILE, ""))
    
    unprocessed.sort(key=sort_key)
    
    logging.info(f"Found {len(unprocessed)} unprocessed records")
    return unprocessed