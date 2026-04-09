"""Conservative FOUND / NOT_FOUND decision logic."""

import logging
from typing import Optional, Tuple

from markphotomediaapprovalstatusautolib.constants import PHASH_THRESHOLD
from markphotomediaapprovalstatusautolib.models import Evidence


def decide(
    evidence: Optional[Evidence],
    phash_threshold: int = PHASH_THRESHOLD,
    combined_threshold: Optional[int] = None,
) -> Tuple[str, str]:
    """Return (outcome, reason) for the given evidence.

    When *combined_threshold* is given the verdict is based on the sum of
    phash_distance + dhash_distance, which is more robust for image variants
    (sharpen, BW, negative) whose pHash alone may be misleading.  When
    *combined_threshold* is None the original phash-only logic is used —
    this keeps the main pipeline conservative.

    :param evidence: Best evidence collected for a candidate, or None when no
        candidates were found.
    :param phash_threshold: Maximum pHash Hamming distance accepted as FOUND
        (used when combined_threshold is None).
    :param combined_threshold: Maximum phash+dhash combined distance accepted
        as FOUND.  When set, overrides phash_threshold check.
    :return: Tuple of outcome string (``"FOUND"`` or ``"NOT_FOUND"``) and a
        machine-readable reason code.
    """
    if evidence is None:
        return "NOT_FOUND", "no_candidates"
    if not evidence.contributor_match:
        return "NOT_FOUND", "contributor_mismatch"
    if evidence.phash_distance is None:
        return "NOT_FOUND", "preview_unavailable"
    if combined_threshold is not None:
        combined = evidence.phash_distance + (evidence.dhash_distance or 999)
        if combined > combined_threshold:
            return "NOT_FOUND", f"combined_distance:{combined}"
        return "FOUND", f"combined:{combined}"
    if evidence.phash_distance > phash_threshold:
        return "NOT_FOUND", f"phash_distance:{evidence.phash_distance}"
    return "FOUND", f"phash:{evidence.phash_distance}"
