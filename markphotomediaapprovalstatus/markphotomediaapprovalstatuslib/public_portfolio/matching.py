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
    """Normalize text for comparison by lowercasing and removing special characters.

    Internal punctuation (commas, periods, semicolons, etc.) is replaced with spaces
    so that URL slugs (which lose punctuation) can match CSV titles that have punctuation.
    """
    if not text:
        return ""
    value = text.lower().strip()
    value = _normalize_separators(value)
    value = re.sub(r"[.,:;!?()\[\]\"']+", " ", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[\s\-\|_/]+$", "", value)
    value = value.strip()
    return value


def _pipe_segments(title: str) -> List[str]:
    """Split a title on ` | ` and return the non-empty segments.

    :param title: Raw title string (not yet normalized).
    :return: List of stripped segments.
    """
    return [seg.strip() for seg in title.split(" | ") if seg.strip()]


def _is_prefix_match(asset_words: List[str], csv_words: List[str]) -> bool:
    """Check whether asset_words is a word-level prefix of csv_words.

    Used to handle URL-slug truncation where the asset title is shorter than
    the full CSV title. Requires at least 4 asset words and coverage of at
    least 35% of the CSV title words to avoid spurious short-title matches.

    :param asset_words: Normalized words from the portfolio asset title.
    :param csv_words: Normalized words from the CSV record title.
    :return: True when asset_words == csv_words[:len(asset_words)] with enough coverage.
    """
    n = len(asset_words)
    if n < 4 or not csv_words:
        return False
    if n > len(csv_words):
        return False
    if n / len(csv_words) < 0.50:
        return False
    return csv_words[:n] == asset_words


def match_record_to_public_assets(
    bank: str,
    contributor_id: str,
    title: str,
    description: str,
    assets: List[PublicAsset],
) -> MatchResult:
    """Match a CSV record to public portfolio assets by title.

    Matching strategy (in order of priority):
    1. Exact normalized title match.
    2. Pipe-split: for CSV titles like "Primary | Subtitle", also try matching
       the primary segment alone (handles banks that only show the primary title).
    3. Prefix match: asset title is a truncated prefix of the CSV title
       (handles URL slugs that are cut off).

    :param bank: Bank name.
    :param contributor_id: Contributor identifier.
    :param title: Title from CSV record.
    :param description: Description from CSV record (used as secondary match).
    :param assets: List of assets from public portfolio.
    :return: MatchResult indicating approval status.
    """
    if not assets:
        return MatchResult(approved=False, matched_by="NONE")

    candidates = [a for a in assets if a.contributor_id == contributor_id]
    if not candidates:
        return MatchResult(approved=False, matched_by="NONE")

    if not title:
        return MatchResult(approved=False, matched_by="NONE")

    normalized_description = normalize_text(description)

    segments = _pipe_segments(title)
    if not segments:
        return MatchResult(approved=False, matched_by="NONE")

    normalized_segments = [normalize_text(s) for s in segments]
    normalized_segments = [s for s in normalized_segments if s]
    if not normalized_segments:
        return MatchResult(approved=False, matched_by="NONE")

    primary_segment = normalized_segments[0]
    csv_words = primary_segment.split()

    def _check_desc(asset_desc: str) -> bool:
        if asset_desc and normalized_description and asset_desc != normalized_description:
            return False
        return True

    for seg in normalized_segments:
        seg_words = seg.split()
        matches = []
        for asset in candidates:
            asset_norm = normalize_text(asset.title)
            asset_desc = normalize_text(asset.description)
            if asset_norm != seg:
                continue
            if not _check_desc(asset_desc):
                continue
            matches.append(asset)
        if len(matches) == 1:
            return MatchResult(approved=True, matched_by="TITLE", public_url=matches[0].url, asset_title=matches[0].title)
        if len(matches) > 1:
            return MatchResult(approved=False, matched_by="AMBIGUOUS")

    for asset in candidates:
        asset_norm = normalize_text(asset.title)
        asset_desc = normalize_text(asset.description)
        if not _check_desc(asset_desc):
            continue
        asset_words = asset_norm.split()
        for seg in normalized_segments:
            seg_words = seg.split()
            if _is_prefix_match(asset_words, seg_words):
                return MatchResult(approved=True, matched_by="TITLE", public_url=asset.url, asset_title=asset.title)

    return MatchResult(approved=False, matched_by="NONE")
