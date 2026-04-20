"""
Prepared date filtering utilities.
"""

from __future__ import annotations

from datetime import datetime, date
import logging
from typing import Dict, List, Optional


def parse_prepared_date(value: str) -> Optional[date]:
    """
    Parse a prepared date value into a date object.

    Args:
        value: Date string in supported formats

    Returns:
        Parsed date or None if invalid/empty
    """
    if not value or not value.strip():
        return None

    candidate = value.strip()

    formats = [
        "%d.%m.%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y:%m:%d %H:%M:%S",
        "%Y:%m:%d",
        "%d.%m.%Y %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(candidate, fmt)
            return parsed.date()
        except ValueError:
            continue

    logging.warning("Could not parse prepared date: %s", value)
    return None


def filter_records_by_prepared_date(
    records: List[Dict[str, str]],
    column_name: str,
    after_date: Optional[date],
    before_date: Optional[date]
) -> List[Dict[str, str]]:
    """
    Filter records by prepared date range.

    Args:
        records: Records to filter
        column_name: Column name containing prepared date
        after_date: Inclusive lower bound
        before_date: Inclusive upper bound

    Returns:
        Filtered records
    """
    if not after_date and not before_date:
        return records

    filtered: List[Dict[str, str]] = []
    for record in records:
        value = record.get(column_name, "")
        record_date = parse_prepared_date(value)
        if record_date is None:
            continue

        if after_date and record_date < after_date:
            continue
        if before_date and record_date > before_date:
            continue

        filtered.append(record)

    logging.info("Prepared date filter kept %d of %d records", len(filtered), len(records))
    return filtered
