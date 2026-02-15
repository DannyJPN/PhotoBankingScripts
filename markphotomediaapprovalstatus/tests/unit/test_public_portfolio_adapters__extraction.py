"""Unit tests for bank adapter HTML extraction (no browser needed)."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

from markphotomediaapprovalstatuslib.public_portfolio.banks.base import BaseBankAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.depositphotos import DepositPhotosAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.rf123 import RF123Adapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.gettyimages import GettyImagesAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.bigstockphoto import BigStockPhotoAdapter
from markphotomediaapprovalstatuslib.public_portfolio.banks.adobestock import AdobeStockAdapter


def _adapter(cls):
    """Instantiate adapter without a real browser context."""
    return cls(browser_context=None)


# ---------------------------------------------------------------------------
# BaseBankAdapter._clean_title
# ---------------------------------------------------------------------------

def test_base__clean_title__removes_stock_photo_suffix():
    adapter = _adapter(BaseBankAdapter)
    assert adapter._clean_title("Sunny meadow stock photo") == "Sunny meadow"


def test_base__clean_title__removes_stock_image_suffix():
    adapter = _adapter(BaseBankAdapter)
    assert adapter._clean_title("Tiger in jungle stock image") == "Tiger in jungle"


def test_base__clean_title__no_suffix_unchanged():
    adapter = _adapter(BaseBankAdapter)
    assert adapter._clean_title("Just a title") == "Just a title"


def test_base__clean_title__strips_whitespace():
    adapter = _adapter(BaseBankAdapter)
    assert adapter._clean_title("  Title  ") == "Title"


def test_base__extract_item_links__deduplicates():
    adapter = _adapter(AdobeStockAdapter)
    html = (
        'href="https://stock.adobe.com/cz/images/photo/123456" '
        'href="https://stock.adobe.com/cz/images/photo/123456" '
        'href="https://stock.adobe.com/cz/images/photo/789012"'
    )
    links = adapter.extract_item_links(html)
    assert len(links) == 2


# ---------------------------------------------------------------------------
# DepositPhotosAdapter
# ---------------------------------------------------------------------------

def test_depositphotos__extract_assets__basic():
    adapter = _adapter(DepositPhotosAdapter)
    html = (
        'src="https://st.depositphotos.com/55998584/86227/i/450/'
        'depositphotos_862275956-stock-photo-two-white-mute-swans-glide.jpg"'
    )
    assets = adapter.extract_assets_from_portfolio(html, "user1")
    assert len(assets) == 1
    assert "two white mute swans glide" in assets[0].title.lower()


def test_depositphotos__extract_assets__deduplicates():
    adapter = _adapter(DepositPhotosAdapter)
    slug = "depositphotos_111111-stock-photo-test-title.jpg"
    html = f'src="{slug}" src="{slug}"'
    assets = adapter.extract_assets_from_portfolio(html, "user1")
    assert len(assets) == 1


def test_depositphotos__extract_assets__skips_short_titles():
    adapter = _adapter(DepositPhotosAdapter)
    html = 'src="depositphotos_111-stock-photo-ab.jpg"'
    assets = adapter.extract_assets_from_portfolio(html, "user1")
    assert len(assets) == 0


# ---------------------------------------------------------------------------
# RF123Adapter
# ---------------------------------------------------------------------------

def test_rf123__extract_assets__from_url_slug():
    adapter = _adapter(RF123Adapter)
    html = '/photo_186683400_beautiful-nature-scene-with-pond.html'
    assets = adapter.extract_assets_from_portfolio(html, "user1")
    assert len(assets) == 1
    assert "beautiful nature scene with pond" in assets[0].title.lower()


def test_rf123__extract_assets__deduplicates():
    adapter = _adapter(RF123Adapter)
    slug = '/photo_12345_test-photo-title.html'
    assets = adapter.extract_assets_from_portfolio(slug * 3, "user1")
    assert len(assets) == 1


# ---------------------------------------------------------------------------
# GettyImagesAdapter
# ---------------------------------------------------------------------------

def test_gettyimages__extract_assets__from_url_slug():
    adapter = _adapter(GettyImagesAdapter)
    html = '/en/photo/wooden-lookout-platform-in-forest-gm123456789-987654321'
    assets = adapter.extract_assets_from_portfolio(html, "user1")
    assert len(assets) == 1
    assert "wooden lookout platform in forest" in assets[0].title.lower()


def test_gettyimages__extract_assets__deduplicates_by_photo_id():
    adapter = _adapter(GettyImagesAdapter)
    slug = '/en/photo/test-title-gm999888777-111222333'
    assets = adapter.extract_assets_from_portfolio(slug * 3, "user1")
    assert len(assets) == 1


def test_gettyimages__extract_assets__skips_logo_from_alt():
    adapter = _adapter(GettyImagesAdapter)
    html = '<img alt="iStock logo large version">'
    assets = adapter.extract_assets_from_portfolio(html, "user1")
    assert all("logo" not in a.title.lower() for a in assets)


# ---------------------------------------------------------------------------
# BigStockPhotoAdapter
# ---------------------------------------------------------------------------

def test_bigstockphoto__extract_assets__basic():
    adapter = _adapter(BigStockPhotoAdapter)
    html = '/image-123456789/beautiful-autumn-forest-with-colorful-leaves'
    assets = adapter.extract_assets_from_portfolio(html, "user1")
    assert len(assets) == 1
    assert "beautiful autumn forest" in assets[0].title.lower()


def test_bigstockphoto__is_supported():
    adapter = _adapter(BigStockPhotoAdapter)
    assert adapter.is_supported() is True


def test_bigstockphoto__extract_assets__deduplicates():
    adapter = _adapter(BigStockPhotoAdapter)
    slug = '/image-111222/test-title-here'
    assets = adapter.extract_assets_from_portfolio(slug * 3, "user1")
    assert len(assets) == 1