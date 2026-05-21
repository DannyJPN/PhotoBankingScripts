"""Unit tests for decision.py."""

import pytest

from markphotomediaapprovalstatusautolib.decision import decide
from markphotomediaapprovalstatusautolib.models import Candidate, Evidence


def _make_candidate() -> Candidate:
    return Candidate(bank="TestBank", url="http://x", preview_url="http://x/p.jpg", contributor_name="alice")


def test_decide__no_evidence_returns_not_found():
    outcome, reason = decide(None)
    assert outcome == "NOT_FOUND"
    assert reason == "no_candidates"


def test_decide__contributor_mismatch_returns_not_found():
    ev = Evidence(candidate=_make_candidate(), phash_distance=0, contributor_match=False)
    outcome, reason = decide(ev)
    assert outcome == "NOT_FOUND"
    assert reason == "contributor_mismatch"


def test_decide__preview_unavailable_returns_not_found():
    ev = Evidence(candidate=_make_candidate(), phash_distance=None, contributor_match=True)
    outcome, reason = decide(ev)
    assert outcome == "NOT_FOUND"
    assert reason == "preview_unavailable"


def test_decide__phash_above_threshold_returns_not_found():
    ev = Evidence(candidate=_make_candidate(), phash_distance=5, contributor_match=True)
    outcome, reason = decide(ev)
    assert outcome == "NOT_FOUND"
    assert "phash_distance:5" in reason


def test_decide__phash_zero_contributor_match_returns_found():
    ev = Evidence(candidate=_make_candidate(), phash_distance=0, contributor_match=True)
    outcome, reason = decide(ev)
    assert outcome == "FOUND"
    assert "phash:0" in reason


def test_decide__phash_at_threshold_returns_found():
    ev = Evidence(candidate=_make_candidate(), phash_distance=2, contributor_match=True)
    outcome, reason = decide(ev)
    assert outcome == "FOUND"


def test_decide__phash_one_above_threshold_returns_not_found():
    ev = Evidence(candidate=_make_candidate(), phash_distance=3, contributor_match=True)
    outcome, reason = decide(ev)
    assert outcome == "NOT_FOUND"