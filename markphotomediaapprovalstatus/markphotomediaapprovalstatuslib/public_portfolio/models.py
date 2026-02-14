"""Data models for public portfolio approval detection."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PublicAsset:
    """Represents a photo asset from a public portfolio page."""

    bank: str
    url: str
    contributor_id: str
    title: str
    description: str


@dataclass
class MatchResult:
    """Result of matching a CSV record to public portfolio assets."""

    approved: bool
    matched_by: str  # "TITLE", "NONE", "AMBIGUOUS"
    public_url: Optional[str] = None
