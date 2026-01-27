"""Data models for public portfolio approval detection."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PublicAsset:
    bank: str
    url: str
    contributor_id: str
    title: str
    description: str
    xid: Optional[str] = None


@dataclass
class MatchResult:
    approved: bool
    matched_by: str  # "XID", "TEXT", "NONE", "AMBIGUOUS"
    public_url: Optional[str] = None
