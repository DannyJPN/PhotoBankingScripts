"""Unit tests for public portfolio matching logic."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

import pytest
from markphotomediaapprovalstatuslib.public_portfolio.matching import (
    normalize_text,
    match_record_to_public_assets,
)
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------

def test_normalize_text__strips_whitespace():
    assert normalize_text("  Hello   World ") == "hello world"


def test_normalize_text__lowercases():
    assert normalize_text("UPPERCASE") == "uppercase"


def test_normalize_text__em_dash_to_hyphen():
    assert normalize_text("A\u2014B") == "a-b"


def test_normalize_text__en_dash_to_hyphen():
    assert normalize_text("A\u2013B") == "a-b"


def test_normalize_text__nbsp_to_space():
    assert normalize_text("A\u00a0B") == "a b"


def test_normalize_text__collapses_spaces():
    assert normalize_text("a  b   c") == "a b c"


def test_normalize_text__strips_trailing_punctuation():
    assert normalize_text("hello world.") == "hello world"


def test_normalize_text__empty_string():
    assert normalize_text("") == ""


def test_normalize_text__none_like_empty():
    assert normalize_text("") == ""


# ---------------------------------------------------------------------------
# match_record_to_public_assets – title match
# ---------------------------------------------------------------------------

def _make_asset(title: str, desc: str = "", contributor: str = "user1") -> PublicAsset:
    return PublicAsset(
        bank="TestBank",
        url="https://example.com/photo/1",
        contributor_id=contributor,
        title=title,
        description=desc,
    )


def test_match__exact_title_returns_approved():
    asset = _make_asset("Sunny meadow in spring")
    result = match_record_to_public_assets("TestBank", "user1", "Sunny meadow in spring", "", [asset])
    assert result.approved is True
    assert result.matched_by == "TITLE"
    assert result.public_url == asset.url


def test_match__case_insensitive():
    asset = _make_asset("Sunny Meadow In Spring")
    result = match_record_to_public_assets("TestBank", "user1", "sunny meadow in spring", "", [asset])
    assert result.approved is True


def test_match__different_title_returns_not_approved():
    asset = _make_asset("Winter forest")
    result = match_record_to_public_assets("TestBank", "user1", "Summer beach", "", [asset])
    assert result.approved is False
    assert result.matched_by == "NONE"


def test_match__empty_title_returns_not_approved():
    asset = _make_asset("Winter forest")
    result = match_record_to_public_assets("TestBank", "user1", "", "", [asset])
    assert result.approved is False
    assert result.matched_by == "NONE"


def test_match__no_assets_returns_not_approved():
    result = match_record_to_public_assets("TestBank", "user1", "Any title", "", [])
    assert result.approved is False
    assert result.matched_by == "NONE"


def test_match__wrong_contributor_returns_not_approved():
    asset = _make_asset("Sunny meadow", contributor="other_user")
    result = match_record_to_public_assets("TestBank", "user1", "Sunny meadow", "", [asset])
    assert result.approved is False
    assert result.matched_by == "NONE"


def test_match__ambiguous_two_same_titles():
    assets = [_make_asset("Same title"), _make_asset("Same title")]
    result = match_record_to_public_assets("TestBank", "user1", "Same title", "", assets)
    assert result.approved is False
    assert result.matched_by == "AMBIGUOUS"


def test_match__description_mismatch_skips():
    asset = _make_asset("Photo", desc="Real description")
    result = match_record_to_public_assets("TestBank", "user1", "Photo", "Different description", [asset])
    assert result.approved is False


def test_match__empty_asset_description_allows_match():
    """Asset without description should still match by title alone."""
    asset = _make_asset("Photo", desc="")
    result = match_record_to_public_assets("TestBank", "user1", "Photo", "Any description", [asset])
    assert result.approved is True


def test_match__unicode_normalization_matches():
    asset = _make_asset("Prase\u2013les")
    result = match_record_to_public_assets("TestBank", "user1", "Prase-les", "", [asset])
    assert result.approved is True