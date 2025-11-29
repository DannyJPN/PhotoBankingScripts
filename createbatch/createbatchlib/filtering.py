import logging
from typing import List, Dict
from tqdm import tqdm
from createbatchlib.constants import STATUS_FIELD_KEYWORD, PREPARED_STATUS_VALUE

def filter_prepared_media(records: List[Dict[str, str]], include_edited: bool = False) -> List[Dict[str, str]]:
    """
    Filter records to include only those marked as PREPARED_STATUS_VALUE in any status field.

    Args:
        records: List of media records from CSV
        include_edited: If False (default), exclude edited photos from 'upravené' folders.
                       If True, include all photos (original and edited).
    """
    total = len(records)
    logging.debug("Starting filtering of prepared media from %d records (include_edited=%s)", total, include_edited)
    filtered: List[Dict[str, str]] = []
    excluded_edited_count = 0

    for record in tqdm(records, total=total, desc="Filtering prepared media", unit="records"):
        # Check if record has PREPARED status
        # NOTE: Using exact match to avoid matching 'nepřipraveno' when looking for 'připraveno'
        has_prepared_status = False
        for key, value in record.items():
            if STATUS_FIELD_KEYWORD in key.lower() and isinstance(value, str) and value.strip().lower() == PREPARED_STATUS_VALUE.lower():
                has_prepared_status = True
                break

        if not has_prepared_status:
            continue

        # Check if it's an edited photo and should be excluded
        if not include_edited:
            file_path = record.get('Cesta', '')
            if file_path and 'upravené' in file_path.lower():
                excluded_edited_count += 1
                logging.debug("Excluding edited photo: %s", file_path)
                continue

        filtered.append(record)

    logging.info("Filtered %d prepared media records out of %d (excluded %d edited photos)",
                 len(filtered), total, excluded_edited_count)
    return filtered