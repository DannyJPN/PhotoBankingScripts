"""Unit tests for public portfolio matching."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

from markphotomediaapprovalstatuslib.public_portfolio.matching import (
    extract_xid,
    normalize_text,
    match_record_to_public_assets,
)
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset


def test_normalize_text__basic():
    assert normalize_text("  Hello   World ") == "hello world"


def test_extract_xid__basic():
    assert extract_xid("Some text xid:ABC123def456") == "xid:abc123def456"


def test_match_record__xid_exact():
    asset = PublicAsset(
        bank="Test",
        url="https://example.com/1",
        contributor_id="user1",
        title="Title xid_abc123",
        description="Desc",
        xid="xid_abc123",
    )
    result = match_record_to_public_assets(
        "Test",
        "user1",
        "Title xid_abc123",
        "Desc",
        [asset],
    )
    assert result.approved is True
    assert result.matched_by == "XID"


def test_match_record__text_exact():
    asset = PublicAsset(
        bank="Test",
        url="https://example.com/2",
        contributor_id="user1",
        title="Exact title",
        description="Exact description",
        xid=None,
    )
    result = match_record_to_public_assets(
        "Test",
        "user1",
        "Exact title",
        "Exact description",
        [asset],
    )
    assert result.approved is True
    assert result.matched_by == "TEXT"


def test_match_record__ambiguous():
    assets = [
        PublicAsset("Test", "url1", "user1", "Same", "Same", None),
        PublicAsset("Test", "url2", "user1", "Same", "Same", None),
    ]
    result = match_record_to_public_assets(
        "Test",
        "user1",
        "Same",
        "Same",
        assets,
    )
    assert result.approved is False
    assert result.matched_by == "AMBIGUOUS"
