"""Unit tests for public portfolio HTML utility functions."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

from markphotomediaapprovalstatuslib.public_portfolio.utils import (
    extract_json_ld,
    extract_from_json_ld,
    extract_meta_content,
    extract_title,
    build_public_asset,
)


# ---------------------------------------------------------------------------
# extract_title
# ---------------------------------------------------------------------------

def test_extract_title__basic():
    html = "<html><head><title>My Page</title></head></html>"
    assert extract_title(html) == "My Page"


def test_extract_title__strips_whitespace():
    html = "<title>  Spaces  </title>"
    assert extract_title(html) == "Spaces"


def test_extract_title__missing_returns_none():
    assert extract_title("<html></html>") is None


# ---------------------------------------------------------------------------
# extract_meta_content
# ---------------------------------------------------------------------------

def test_extract_meta_content__og_title():
    html = '<meta property="og:title" content="Great Photo">'
    assert extract_meta_content(html, "og:title") == "Great Photo"


def test_extract_meta_content__og_description():
    html = '<meta property="og:description" content="Photo of a dog">'
    assert extract_meta_content(html, "og:description") == "Photo of a dog"


def test_extract_meta_content__missing_returns_none():
    assert extract_meta_content("<html></html>", "og:title") is None


# ---------------------------------------------------------------------------
# extract_json_ld
# ---------------------------------------------------------------------------

def test_extract_json_ld__single_block():
    html = """
    <script type="application/ld+json">{"@type": "ImageObject", "name": "Tiger"}</script>
    """
    blocks = extract_json_ld(html)
    assert len(blocks) == 1
    assert blocks[0]["name"] == "Tiger"


def test_extract_json_ld__list_block():
    html = """
    <script type="application/ld+json">[{"name": "A"}, {"name": "B"}]</script>
    """
    blocks = extract_json_ld(html)
    assert len(blocks) == 2


def test_extract_json_ld__invalid_json_skipped():
    html = '<script type="application/ld+json">{invalid json}</script>'
    blocks = extract_json_ld(html)
    assert blocks == []


def test_extract_json_ld__no_scripts():
    assert extract_json_ld("<html></html>") == []


# ---------------------------------------------------------------------------
# extract_from_json_ld
# ---------------------------------------------------------------------------

def test_extract_from_json_ld__title_and_description():
    html = """
    <script type="application/ld+json">
    {"@type": "ImageObject", "name": "Sunset", "description": "Colorful sunset"}
    </script>
    """
    result = extract_from_json_ld(html)
    assert result["title"] == "Sunset"
    assert result["description"] == "Colorful sunset"


def test_extract_from_json_ld__author_as_dict():
    html = """
    <script type="application/ld+json">
    {"name": "Photo", "author": {"name": "John"}}
    </script>
    """
    result = extract_from_json_ld(html)
    assert result["author"] == "John"


def test_extract_from_json_ld__author_as_list():
    html = """
    <script type="application/ld+json">
    {"name": "Photo", "author": [{"name": "Jane"}]}
    </script>
    """
    result = extract_from_json_ld(html)
    assert result["author"] == "Jane"


def test_extract_from_json_ld__empty_html():
    result = extract_from_json_ld("")
    assert result["title"] is None
    assert result["description"] is None
    assert result["author"] is None


# ---------------------------------------------------------------------------
# build_public_asset
# ---------------------------------------------------------------------------

def test_build_public_asset__basic():
    asset = build_public_asset("TestBank", "http://x.com/1", "user1", "Title", "Desc")
    assert asset["bank"] == "TestBank"
    assert asset["url"] == "http://x.com/1"
    assert asset["contributor_id"] == "user1"
    assert asset["title"] == "Title"
    assert asset["description"] == "Desc"


def test_build_public_asset__empty_title_defaults_empty_string():
    asset = build_public_asset("Bank", "url", "user", "", "")
    assert asset["title"] == ""
    assert asset["description"] == ""


def test_build_public_asset__no_xid_field():
    asset = build_public_asset("Bank", "url", "user", "Title", "Desc")
    assert "xid" not in asset