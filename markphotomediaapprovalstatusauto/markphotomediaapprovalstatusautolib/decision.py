"""Conservative FOUND / NOT_FOUND decision logic."""

import logging
from typing import Optional, Tuple

from markphotomediaapprovalstatusautolib.constants import PHASH_THRESHOLD
from markphotomediaapprovalstatusautolib.models import Evidence


def decide(evidence: Optional[Evidence], phash_threshold: int = PHASH_THRESHOLD) -> Tuple[str, str]:
    """Return (outcome, reason) for the given evidence.

    :param evidence: Best evidence collected for a candidate, or None when no
        candidates were found.
    :param phash_threshold: Maximum Hamming distance accepted as FOUND.
    :return: Tuple of outcome string (``"FOUND"`` or ``"NOT_FOUND"``) and a
        machine-readable reason code.
    """
    if evidence is None:
        return "NOT_FOUND", "no_candidates"
    if not evidence.contributor_match:
        return "NOT_FOUND", "contributor_mismatch"
    if evidence.phash_distance is None:
        return "NOT_FOUND", "preview_unavailable"
    if evidence.phash_distance > phash_threshold:
        return "NOT_FOUND", f"phash_distance:{evidence.phash_distance}"
    return "FOUND", f"phash:{evidence.phash_distance}"
