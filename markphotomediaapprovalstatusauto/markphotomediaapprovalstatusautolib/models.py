"""Data models for automatic public portfolio detection pipeline."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class PhotoRecord:
    """A single row from PhotoMedia.csv enriched with a local file path."""

    file: str
    path: str
    title: str
    description: str
    keywords: str
    bank_statuses: Dict[str, str]
    local_file_path: str


@dataclass
class Candidate:
    """An asset discovered on a photobank that may match a PhotoRecord."""

    bank: str
    url: str
    preview_url: str
    contributor_name: str
    asset_id: Optional[str] = None
    title: str = ""


@dataclass
class Evidence:
    """Verification signals collected for a single Candidate."""

    candidate: "Candidate"
    phash_distance: Optional[int] = None
    dhash_distance: Optional[int] = None
    contributor_match: bool = False
    dimension_match: Optional[bool] = None


@dataclass
class DetectionResult:
    """Final outcome for one PhotoRecord × bank pair."""

    record_file: str
    bank: str
    outcome: str
    matched_url: Optional[str] = None
    matched_id: Optional[str] = None
    evidence: Optional["Evidence"] = None
    reason: str = ""
    timestamp: str = ""
