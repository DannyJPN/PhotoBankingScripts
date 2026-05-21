"""Audit entry data model for detection pipeline results."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AuditEntry:
    """One row in the detection audit report.

    Every discovery attempt — whether FOUND or NOT_FOUND — produces one
    AuditEntry.  This ensures a complete audit trail for all processed records.
    """

    timestamp: str
    local_file: str
    bank: str
    result: str
    candidate_url: Optional[str]
    candidate_id: Optional[str]
    contributor_match: Optional[bool]
    phash_distance: Optional[int]
    dhash_distance: Optional[int]
    dimension_match: Optional[bool]
    preview_url: Optional[str]
    reason: str