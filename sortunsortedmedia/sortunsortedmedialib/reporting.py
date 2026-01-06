"""
Reporting helpers for SortUnsortedMedia.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List


def build_detail_records(unmatched_categories: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """
    Build detailed report records for unmatched files.

    Args:
        unmatched_categories: Mapping of category name to list of file paths

    Returns:
        List of dicts with category and file path
    """
    records: List[Dict[str, str]] = []
    for category, files in unmatched_categories.items():
        for file_path in files:
            records.append({"category": category, "file_path": file_path})
    return records


def build_summary_records(unmatched_categories: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """
    Build summary records for unmatched files.

    Args:
        unmatched_categories: Mapping of category name to list of file paths

    Returns:
        List of dicts with category and count
    """
    summary: List[Dict[str, str]] = []
    total_count = 0
    for category, files in unmatched_categories.items():
        count = len(files)
        total_count += count
        summary.append({"category": category, "count": str(count)})
    summary.append({"category": "total", "count": str(total_count)})
    return summary


def build_report_filename(prefix: str, extension: str) -> str:
    """
    Build a timestamped report filename.

    Args:
        prefix: File prefix to use
        extension: File extension without dot

    Returns:
        Filename with timestamp and extension
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{prefix}_{timestamp}.{extension}"
