"""Title-based matching for public portfolio approval detection."""

from __future__ import annotations

import re
from typing import List

from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset, MatchResult


def _normalize_separators(text: str) -> str:
    """Replace Unicode dashes, quotes and non-breaking spaces with ASCII equivalents.

    :param text: Input string that may contain Unicode punctuation.
    :return: String with typographic characters replaced by plain ASCII equivalents.
    """
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
    """Normalize text for comparison by lowercasing and removing special characters."""
    if not text:
        return ""
    value = text.lower().strip()
    value = _normalize_separators(value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[\s\-\|_/]+$", "", value)
    value = value.strip(" .,:;!?)\"'\n\t")
    return value


def match_record_to_public_assets(
    bank: str,
    contributor_id: str,
    title: str,
    description: str,
    assets: List[PublicAsset],
) -> MatchResult:
    """Match a CSV record to public portfolio assets by title.

    :param bank: Bank name.
    :param contributor_id: Contributor identifier.
    :param title: Title from CSV record.
    :param description: Description from CSV record (used as secondary match).
    :param assets: List of assets from public portfolio.
    :return: MatchResult indicating approval status.
    """
    if not assets:
        return MatchResult(approved=False, matched_by="NONE")

    normalized_title = normalize_text(title)
    normalized_description = normalize_text(description)

    candidates = [a for a in assets if a.contributor_id == contributor_id]
    if not candidates:
        return MatchResult(approved=False, matched_by="NONE")

    if not normalized_title:
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
        return MatchResult(approved=True, matched_by="TITLE", public_url=matches[0].url)
    if len(matches) > 1:
        return MatchResult(approved=False, matched_by="AMBIGUOUS")

    return MatchResult(approved=False, matched_by="NONE")
