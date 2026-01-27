"""Deterministic matching for public portfolio approval detection."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset, MatchResult


XID_PATTERN = re.compile(r"(?:\\b|\\s)(xid[:_\\-]?[a-f0-9]{6,32})\\b", re.IGNORECASE)


def extract_xid(text: str) -> Optional[str]:
    if not text:
        return None
    match = XID_PATTERN.search(text)
    if not match:
        return None
    xid = match.group(1).lower()
    return xid


def _normalize_separators(text: str) -> str:
    replacements = {
        "\u2010": "-",  # hyphen
        "\u2011": "-",  # non-breaking hyphen
        "\u2012": "-",  # figure dash
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2015": "-",  # horizontal bar
        "\u2212": "-",  # minus
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201c": "\"",  # left double quote
        "\u201d": "\"",  # right double quote
        "\u00a0": " ",  # non-breaking space
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def normalize_text(text: str) -> str:
    if not text:
        return ""
    value = text.lower().strip()
    value = _normalize_separators(value)
    value = re.sub(r"\\s+", " ", value)
    value = re.sub(r"[\\s\\-\\|_/]+$", "", value)
    value = value.strip(" .,:;!?)\"'\\n\\t")
    return value


def build_public_index(assets: List[PublicAsset]) -> Dict[Tuple[str, str], List[PublicAsset]]:
    index: Dict[Tuple[str, str], List[PublicAsset]] = {}
    for asset in assets:
        key = (
            normalize_text(asset.title),
            normalize_text(asset.description),
        )
        index.setdefault(key, []).append(asset)
    return index


def match_record_to_public_assets(
    bank: str,
    contributor_id: str,
    title: str,
    description: str,
    assets: List[PublicAsset],
) -> MatchResult:
    if not assets:
        return MatchResult(approved=False, matched_by="NONE")

    normalized_title = normalize_text(title)
    normalized_description = normalize_text(description)
    local_xid = extract_xid(f"{title} {description}")

    candidates = [a for a in assets if a.contributor_id == contributor_id]
    if not candidates:
        return MatchResult(approved=False, matched_by="NONE")

    if local_xid:
        for asset in candidates:
            if asset.xid and asset.xid == local_xid:
                return MatchResult(approved=True, matched_by="XID", public_url=asset.url)

    if not normalized_title and not normalized_description:
        return MatchResult(approved=False, matched_by="NONE")

    matches = []
    for asset in candidates:
        asset_title = normalize_text(asset.title)
        asset_desc = normalize_text(asset.description)
        if asset_title != normalized_title:
            continue
        if asset_desc and normalized_description and asset_desc != normalized_description:
            continue
        matches.append(asset)

    if len(matches) == 1:
        return MatchResult(approved=True, matched_by="TEXT", public_url=matches[0].url)
    if len(matches) > 1:
        return MatchResult(approved=False, matched_by="AMBIGUOUS")

    return MatchResult(approved=False, matched_by="NONE")
