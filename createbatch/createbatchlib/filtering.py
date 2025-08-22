import logging

from createbatchlib.constants import PREPARED_STATUS_VALUE, STATUS_FIELD_KEYWORD
from tqdm import tqdm


def filter_prepared_media(records: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Filter records to include only those marked as PREPARED_STATUS_VALUE in any status field.
    """
    total = len(records)
    logging.debug("Starting filtering of prepared media from %d records", total)
    filtered: list[dict[str, str]] = []
    for record in tqdm(records, total=total, desc="Filtering prepared media", unit="records"):
        for key, value in record.items():
            if (
                STATUS_FIELD_KEYWORD in key.lower()
                and isinstance(value, str)
                and PREPARED_STATUS_VALUE.lower() in value.lower()
            ):
                filtered.append(record)
                break
    logging.info("Filtered %d prepared media records out of %d", len(filtered), total)
    return filtered
