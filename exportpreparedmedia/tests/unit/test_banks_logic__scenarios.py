"""
Unit tests for exportpreparedmedialib/banks_logic.py.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

import exportpreparedmedialib.banks_logic as banks_logic
from exportpreparedmedialib import constants as exp_constants


def test_get_enabled_banks__maps_flags():
    args = SimpleNamespace(
        shutterstock=True,
        adobestock=True,
        dreamstime=False,
        depositphotos=False,
        bigstockphoto=False,
        _123rf=True,
        canstockphoto=False,
        pond5=False,
        gettyimages=False,
        alamy=False,
    )

    banks = banks_logic.get_enabled_banks(args)

    assert banks == ["ShutterStock", "AdobeStock", "123RF"]


def test_get_output_paths__builds_paths(tmp_path):
    output = banks_logic.get_output_paths(["ShutterStock"], str(tmp_path), "CSV")

    assert output["ShutterStock"].endswith("CSV_ShutterStock.csv")


def test_should_include_item__bank_specific_status():
    item = {"ShutterStock Status": exp_constants.VALID_STATUS}
    assert banks_logic.should_include_item(item, bank="ShutterStock") is True


def test_should_include_item__general_status():
    item = {"Some Status": exp_constants.VALID_STATUS}
    assert banks_logic.should_include_item(item) is True


def test_should_include_item__missing_status_false():
    item = {"Title": "x"}
    assert banks_logic.should_include_item(item) is False


def test_load_category_map__returns_map(monkeypatch):
    monkeypatch.setattr(banks_logic, "load_csv", lambda _p: [{"k": "a", "v": "1"}])

    result = banks_logic.load_category_map("file.csv", "k", "v")

    assert result == {"a": "1"}


def test_load_category_map__error_returns_empty(monkeypatch):
    def fail_load(_p):
        raise OSError("fail")

    monkeypatch.setattr(banks_logic, "load_csv", fail_load)
    assert banks_logic.load_category_map("file.csv", "k", "v") == {}


def test_load_pond_prices__defaults_on_error(monkeypatch):
    def fail_load(_p):
        raise OSError("fail")

    monkeypatch.setattr(banks_logic, "load_csv", fail_load)
    prices = banks_logic.load_pond_prices("file.csv")

    assert prices.get("jpg") == "5"
    assert prices.get("mp4") == "30"


def test_remove_duplicate_keywords__removes_short_and_dups():
    result = banks_logic.remove_duplicate_keywords("a, aa, cat, cat, dog, do")
    assert "cat" in result
    assert "dog" in result
    assert "aa" not in result


def test_get_pond_price__default_rules():
    assert banks_logic.get_pond_price("file.tif") == "10"
    assert banks_logic.get_pond_price("file.mp4") == "30"
    assert banks_logic.get_pond_price("file.jpg") == "5"


def test_get_pond_price__map_override():
    prices = {"jpg": "7"}
    assert banks_logic.get_pond_price("file.jpg", prices) == "7"


def test_extract_media_properties__basic_fields():
    item = {
        "Soubor": "photo.jpg",
        "N zev": "Title",
        "Popis": "Desc",
        "Kl¡Ÿov  slova": "cat, dog, cat",
        "Datum vytvoýen¡": "01.02.2020",
    }

    result = banks_logic.extract_media_properties(item, category_maps={})

    assert result["filename"] == "photo.jpg"
    assert result["title"] == "Title"
    assert result["description"] == "Desc"
    assert result["year"] == "2020"
    assert result["getty_date"].startswith("02/01/2020")
