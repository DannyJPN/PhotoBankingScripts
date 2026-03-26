"""Unit tests for the Pond5 discovery adapter."""

from unittest.mock import MagicMock, patch

import pytest

from markphotomediaapprovalstatusautolib.discovery.banks.pond5 import (
    Pond5Adapter,
    build_cdn_preview_url,
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


# --- build_cdn_preview_url ---

def test_build_cdn_preview_url__zero_pads_to_9_digits():
    url = build_cdn_preview_url(123456)
    assert url == "https://ec.pond5.com/s3/000123456_iconm.jpeg"


def test_build_cdn_preview_url__single_digit():
    url = build_cdn_preview_url(1)
    assert url == "https://ec.pond5.com/s3/000000001_iconm.jpeg"


def test_build_cdn_preview_url__9_digit_id_no_padding():
    url = build_cdn_preview_url(123456789)
    assert url == "https://ec.pond5.com/s3/123456789_iconm.jpeg"


def test_build_cdn_preview_url__returns_https():
    url = build_cdn_preview_url(1000)
    assert url.startswith("https://ec.pond5.com/s3/")


# --- Pond5Adapter.discover ---

def test_discover__returns_empty_without_portfolio_index():
    adapter = Pond5Adapter()
    result = adapter.discover(_make_record())
    assert result == []


def test_discover__returns_empty_when_portfolio_index_is_none():
    adapter = Pond5Adapter()
    result = adapter.discover(_make_record(), portfolio_index=None)
    assert result == []


def test_discover__returns_empty_when_portfolio_index_is_empty_list():
    adapter = Pond5Adapter()
    result = adapter.discover(_make_record(), portfolio_index=[])
    assert result == []


def test_discover__returns_one_candidate_per_portfolio_asset():
    index = [(111111, "https://ec.pond5.com/s3/000111111_iconm.jpeg"),
             (222222, "https://ec.pond5.com/s3/000222222_iconm.jpeg")]
    adapter = Pond5Adapter()
    result = adapter.discover(_make_record(), portfolio_index=index, contributor_name="alice")
    assert len(result) == 2


def test_discover__candidate_has_correct_asset_id():
    index = [(987654, "https://ec.pond5.com/s3/000987654_iconm.jpeg")]
    adapter = Pond5Adapter()
    candidates = adapter.discover(_make_record(), portfolio_index=index, contributor_name="alice")
    assert candidates[0].asset_id == "987654"


def test_discover__candidate_has_correct_preview_url():
    cdn_url = "https://ec.pond5.com/s3/000111111_iconm.jpeg"
    index = [(111111, cdn_url)]
    adapter = Pond5Adapter()
    candidates = adapter.discover(_make_record(), portfolio_index=index, contributor_name="alice")
    assert candidates[0].preview_url == cdn_url


def test_discover__candidate_contributor_name_matches_kwarg():
    index = [(111111, "https://ec.pond5.com/s3/000111111_iconm.jpeg")]
    adapter = Pond5Adapter()
    candidates = adapter.discover(_make_record(), portfolio_index=index, contributor_name="bob")
    assert candidates[0].contributor_name == "bob"


def test_discover__candidate_bank_is_pond5():
    index = [(111111, "https://ec.pond5.com/s3/000111111_iconm.jpeg")]
    adapter = Pond5Adapter()
    candidates = adapter.discover(_make_record(), portfolio_index=index, contributor_name="alice")
    assert candidates[0].bank == "Pond5"


def test_discover__candidate_url_contains_asset_id():
    index = [(555000, "https://ec.pond5.com/s3/000555000_iconm.jpeg")]
    adapter = Pond5Adapter()
    candidates = adapter.discover(_make_record(), portfolio_index=index, contributor_name="alice")
    assert "555000" in candidates[0].url


def test_pond5_adapter__bank_name():
    assert Pond5Adapter().bank_name == "Pond5"
