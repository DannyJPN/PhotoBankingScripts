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


# ---------------------------------------------------------------------------
# normalize_text – internal punctuation stripping (new behaviour)
# ---------------------------------------------------------------------------

def test_normalize_text__strips_internal_comma():
    assert normalize_text("cat, dog") == "cat dog"


def test_normalize_text__strips_internal_period():
    assert normalize_text("meadow. forest") == "meadow forest"


def test_normalize_text__strips_trailing_comma():
    assert normalize_text("hello world,") == "hello world"


def test_normalize_text__slug_matches_csv_with_punct():
    """URL slug without comma/period should match CSV title that has them."""
    slug_title = "vertical panoramic image of mountain meadow ski slope in beskydy in summer"
    csv_title = "Vertical panoramic image of mountain meadow. Ski slope in Beskydy in summer."
    assert normalize_text(slug_title) == normalize_text(csv_title)


# ---------------------------------------------------------------------------
# match_record_to_public_assets – pipe-split and prefix matching
# ---------------------------------------------------------------------------

def test_match__pipe_split_matches_primary_segment():
    """Portfolio title matching only the primary CSV segment should approve."""
    asset = _make_asset("Wooden statue of honeybee lying on grass in zoo ostrava")
    csv_title = "Wooden statue of honeybee lying on grass in ZOO Ostrava | Giant insect sculpture"
    result = match_record_to_public_assets("TestBank", "user1", csv_title, "", [asset])
    assert result.approved is True


def test_match__pipe_split_matches_secondary_segment():
    """Portfolio title matching the secondary segment should also approve."""
    asset = _make_asset("Giant insect sculpture")
    csv_title = "Wooden statue of honeybee | Giant insect sculpture"
    result = match_record_to_public_assets("TestBank", "user1", csv_title, "", [asset])
    assert result.approved is True


def test_match__prefix_match_approves_truncated_slug():
    """Slug-derived title that is a word-level prefix of CSV title should match."""
    asset = _make_asset("Skeleton of ancient terror bird phorusrhacos at zoo ostrava")
    csv_title = "Skeleton of ancient terror bird phorusrhacos at zoo ostrava forests"
    result = match_record_to_public_assets("TestBank", "user1", csv_title, "", [asset])
    assert result.approved is True


def test_match__prefix_too_short_does_not_match():
    """A 3-word asset title must not trigger a prefix match (below 4-word minimum)."""
    asset = _make_asset("Cat in hat")
    csv_title = "Cat in hat and other stories from dr seuss universe"
    result = match_record_to_public_assets("TestBank", "user1", csv_title, "", [asset])
    assert result.approved is False


def test_match__prefix_coverage_too_low_does_not_match():
    """Asset title covering < 50 % of CSV words must not match via prefix."""
    asset = _make_asset("Beautiful forest with trees")
    csv_title = (
        "Beautiful forest with trees and sunshine but also rivers "
        "lakes mountains and many more geographical features"
    )
    result = match_record_to_public_assets("TestBank", "user1", csv_title, "", [asset])
    assert result.approved is False