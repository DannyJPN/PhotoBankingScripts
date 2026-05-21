"""Unit tests for the Pond5 discovery adapter."""

import pytest

from markphotomediaapprovalstatusautolib.discovery.banks.pond5 import (
    Pond5Adapter,
    _build_page_url,
    _extract_assets_from_html,
    extract_contributor_name,
)
from markphotomediaapprovalstatusautolib.models import PhotoRecord


def _make_record(**kwargs) -> PhotoRecord:
    defaults = dict(
        file="DSC00001.JPG",
        path="/photos",
        title="Test",
        description="",
        keywords="",
        bank_statuses={"Pond5": "kontrolováno"},
        local_file_path="/photos/DSC00001.JPG",
    )
    defaults.update(kwargs)
    return PhotoRecord(**defaults)


# --- extract_contributor_name ---

def test_extract_contributor_name__extracts_from_standard_url():
    url = "https://www.pond5.com/artist/dannyjpn?tab=photo&pp=1&sb=6"
    assert extract_contributor_name(url) == "dannyjpn"


def test_extract_contributor_name__extracts_without_query_params():
    url = "https://www.pond5.com/artist/johndoe"
    assert extract_contributor_name(url) == "johndoe"


def test_extract_contributor_name__returns_empty_on_no_match():
    assert extract_contributor_name("https://www.pond5.com/search") == ""


# --- _extract_assets_from_html ---

def test_extract_assets_from_html__finds_single_asset():
    html = 'src="https://images.pond5.com/some-photo-123456789_iconl_nowm.jpeg"'
    assets = _extract_assets_from_html(html)
    assert len(assets) == 1
    assert assets[0][0] == 123456789
    assert "_iconl_nowm.jpeg" in assets[0][1]


def test_extract_assets_from_html__finds_multiple_assets():
    html = (
        'src="https://images.pond5.com/cat-photo-111111111_iconl_nowm.jpeg" '
        'src="https://images.pond5.com/dog-photo-222222222_iconl_nowm.jpeg"'
    )
    assets = _extract_assets_from_html(html)
    assert len(assets) == 2


def test_extract_assets_from_html__deduplicates_same_id():
    html = (
        'src="https://images.pond5.com/cat-photo-111111111_iconl_nowm.jpeg" '
        'src="https://images.pond5.com/cat-photo-111111111_iconl_nowm.jpeg"'
    )
    assets = _extract_assets_from_html(html)
    assert len(assets) == 1


def test_extract_assets_from_html__returns_full_cdn_url():
    cdn = "https://images.pond5.com/mountain-sunset-photo-327093691_iconl_nowm.jpeg"
    html = f'src="{cdn}"'
    assets = _extract_assets_from_html(html)
    assert assets[0][1] == cdn


def test_extract_assets_from_html__empty_html_returns_empty():
    assert _extract_assets_from_html("") == []


def test_extract_assets_from_html__ignores_watermarked_variant():
    html = 'src="https://images.pond5.com/cat-photo-111111111_iconl.jpeg"'
    assets = _extract_assets_from_html(html)
    assert len(assets) == 0


def test_extract_assets_from_html__captures_ten_digit_id():
    html = 'src="https://images.pond5.com/cat-photo-1234567890_iconl_nowm.jpeg"'
    assets = _extract_assets_from_html(html)
    assert len(assets) == 1
    assert assets[0][0] == 1234567890


def test_extract_assets_from_html__captures_twelve_digit_id():
    html = 'src="https://images.pond5.com/cat-photo-123456789012_iconl_nowm.jpeg"'
    assets = _extract_assets_from_html(html)
    assert len(assets) == 1
    assert assets[0][0] == 123456789012


# --- _build_page_url ---

def test_build_page_url__sets_page_number():
    url = "https://www.pond5.com/artist/dannyjpn?tab=photo&pp=1&sb=6"
    result = _build_page_url(url, 5)
    assert "pp=5" in result


def test_build_page_url__replaces_existing_pp():
    url = "https://www.pond5.com/artist/dannyjpn?tab=photo&pp=1&sb=6"
    result = _build_page_url(url, 10)
    assert "pp=10" in result
    assert "pp=1&" not in result


def test_build_page_url__keeps_tab_param():
    url = "https://www.pond5.com/artist/dannyjpn?tab=photo&pp=1&sb=6"
    result = _build_page_url(url, 2)
    assert "tab=photo" in result


def test_build_page_url__sb_override_replaces_existing():
    url = "https://www.pond5.com/artist/dannyjpn?tab=photo&pp=1&sb=6"
    result = _build_page_url(url, 1, sb="1")
    assert "sb=1" in result
    assert "sb=6" not in result


def test_build_page_url__sb_none_keeps_original():
    url = "https://www.pond5.com/artist/dannyjpn?tab=photo&pp=1&sb=6"
    result = _build_page_url(url, 1, sb=None)
    assert "sb=6" in result


# --- Pond5Adapter.discover ---

def test_discover__returns_empty_without_portfolio_index():
    assert Pond5Adapter().discover(_make_record()) == []


def test_discover__returns_empty_when_portfolio_index_is_none():
    assert Pond5Adapter().discover(_make_record(), portfolio_index=None) == []


def test_discover__returns_empty_when_portfolio_index_is_empty_list():
    assert Pond5Adapter().discover(_make_record(), portfolio_index=[]) == []


def test_discover__returns_one_candidate_per_portfolio_asset():
    cdn = "https://images.pond5.com/cat-photo-111111111_iconl_nowm.jpeg"
    index = [(111111111, cdn), (222222222, cdn)]
    result = Pond5Adapter().discover(_make_record(), portfolio_index=index, contributor_name="alice")
    assert len(result) == 2


def test_discover__candidate_has_correct_asset_id():
    cdn = "https://images.pond5.com/cat-photo-987654321_iconl_nowm.jpeg"
    candidates = Pond5Adapter().discover(_make_record(), portfolio_index=[(987654321, cdn)], contributor_name="alice")
    assert candidates[0].asset_id == "987654321"


def test_discover__candidate_has_correct_preview_url():
    cdn = "https://images.pond5.com/cat-photo-111111111_iconl_nowm.jpeg"
    candidates = Pond5Adapter().discover(_make_record(), portfolio_index=[(111111111, cdn)], contributor_name="alice")
    assert candidates[0].preview_url == cdn


def test_discover__candidate_contributor_name_matches_kwarg():
    cdn = "https://images.pond5.com/cat-photo-111111111_iconl_nowm.jpeg"
    candidates = Pond5Adapter().discover(_make_record(), portfolio_index=[(111111111, cdn)], contributor_name="bob")
    assert candidates[0].contributor_name == "bob"


def test_discover__candidate_bank_is_pond5():
    cdn = "https://images.pond5.com/cat-photo-111111111_iconl_nowm.jpeg"
    candidates = Pond5Adapter().discover(_make_record(), portfolio_index=[(111111111, cdn)], contributor_name="alice")
    assert candidates[0].bank == "Pond5"


def test_pond5_adapter__bank_name():
    assert Pond5Adapter().bank_name == "Pond5"