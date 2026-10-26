"""
Unit tests for givephotobankreadymediafileslib/editorial_dialog.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import editorial_dialog


class DummyEntry:
    def __init__(self, value=""):
        self._value = value
        self.focused = False

    def get(self):
        return self._value

    def focus(self):
        self.focused = True

    def delete(self, _first, _last=None):
        self._value = ""

    def insert(self, _index, text):
        self._value = text


class DummyDialog:
    def __init__(self):
        self.destroyed = False

    def destroy(self):
        self.destroyed = True


def test_validate_date_format__valid_and_invalid():
    dialog = editorial_dialog.EditorialMetadataDialog.__new__(editorial_dialog.EditorialMetadataDialog)

    assert dialog.validate_date_format("15 03 2024") is True
    assert dialog.validate_date_format("32 01 2024") is False
    assert dialog.validate_date_format("15-03-2024") is False


def test_on_ok__missing_field(monkeypatch):
    dialog = editorial_dialog.EditorialMetadataDialog.__new__(editorial_dialog.EditorialMetadataDialog)
    dialog.entries = {"city": DummyEntry("")}
    dialog.dialog = DummyDialog()
    dialog.result = None

    called = []
    monkeypatch.setattr(editorial_dialog.messagebox, "showerror", lambda *_a, **_k: called.append(True))

    dialog.on_ok()
    assert called
    assert dialog.result is None


def test_on_ok__invalid_date(monkeypatch):
    dialog = editorial_dialog.EditorialMetadataDialog.__new__(editorial_dialog.EditorialMetadataDialog)
    dialog.entries = {"date": DummyEntry("99 99 2024")}
    dialog.dialog = DummyDialog()
    dialog.result = None

    called = []
    monkeypatch.setattr(editorial_dialog.messagebox, "showerror", lambda *_a, **_k: called.append(True))

    dialog.on_ok()
    assert called
    assert dialog.result is None


def test_on_ok__success():
    dialog = editorial_dialog.EditorialMetadataDialog.__new__(editorial_dialog.EditorialMetadataDialog)
    dialog.entries = {"city": DummyEntry("Prague")}
    dialog.dialog = DummyDialog()
    dialog.result = None

    dialog.on_ok()
    assert dialog.result == {"city": "Prague"}
    assert dialog.dialog.destroyed is True


def test_get_editorial_metadata__delegates(monkeypatch):
    class Dummy:
        def __init__(self, *_a, **_k):
            return None

        def show_and_get_result(self):
            return {"city": "Prague"}

    monkeypatch.setattr(editorial_dialog, "EditorialMetadataDialog", Dummy)
    result = editorial_dialog.get_editorial_metadata(object(), {"city": True})
    assert result == {"city": "Prague"}


def test_format_editorial_prefix__uppercase():
    result = editorial_dialog.format_editorial_prefix("Prague", "Czechia", "01 01 2024")
    assert result == "PRAGUE, CZECHIA - 01 01 2024:"


def test_extract_editorial_metadata_from_exif__with_date(monkeypatch):
    class DummyImage:
        def _getexif(self):
            return {306: "2024:01:02 10:11:12"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    import PIL.Image as pil_image
    import PIL.ExifTags as pil_exif_tags

    monkeypatch.setattr(pil_image, "open", lambda _p: DummyImage())
    monkeypatch.setattr(pil_exif_tags, "TAGS", {306: "DateTime"})

    data, missing = editorial_dialog.extract_editorial_metadata_from_exif("C:/file.jpg")
    assert data["date"] == "02 01 2024"
    assert missing["date"] is False


def test_extract_editorial_metadata_from_exif__exception(monkeypatch):
    def raise_error(_p):
        raise OSError("bad file")

    import PIL.Image as pil_image

    monkeypatch.setattr(pil_image, "open", raise_error)
    data, missing = editorial_dialog.extract_editorial_metadata_from_exif("C:/file.jpg")
    assert data == {}
    assert all(missing.values())


@pytest.mark.parametrize(
    "typed, expected",
    [
        ("Žďár nad Sázavou", "Zdar nad Sazavou"),
        ("Frýdek-Místek", "Frydek-Mistek"),
        ("Łódź", "Lodz"),
        ("Straße", "Strasse"),
        ("  Česká   Lípa ", "Ceska Lipa"),
        ("Prague", "Prague"),
    ],
)
def test_transliterate_to_ascii__removes_diacritics(typed, expected):
    assert editorial_dialog.transliterate_to_ascii(typed) == expected


@pytest.mark.parametrize(
    "field, value, expected",
    [
        ("city", "Frenstat pod Radhostem", True),
        ("city", "Frydek-Mistek", True),
        ("city", "St. Petersburg", False),
        ("city", "Brno2", False),
        ("city", "Žilina", False),
        ("country", "Czech", True),
        ("country", "Czech Republic", False),
    ],
)
def test_is_valid_place_name__ascii_letters_only(field, value, expected):
    assert editorial_dialog.is_valid_place_name(field, value) is expected


def test_on_ok__transliterates_city_and_country():
    dialog = editorial_dialog.EditorialMetadataDialog.__new__(editorial_dialog.EditorialMetadataDialog)
    dialog.entries = {
        "city": DummyEntry("Frýdek-Místek"),
        "country": DummyEntry("Česko"),
        "date": DummyEntry("15 03 2024"),
    }
    dialog.dialog = DummyDialog()
    dialog.result = None

    dialog.on_ok()
    assert dialog.result == {"city": "Frydek-Mistek", "country": "Cesko", "date": "15 03 2024"}
    assert dialog.dialog.destroyed is True


def test_on_ok__rejects_invalid_city_characters(monkeypatch):
    dialog = editorial_dialog.EditorialMetadataDialog.__new__(editorial_dialog.EditorialMetadataDialog)
    entry = DummyEntry("Šternberk2")
    dialog.entries = {"city": entry}
    dialog.dialog = DummyDialog()
    dialog.result = None

    messages = []
    monkeypatch.setattr(editorial_dialog.messagebox, "showerror", lambda *a, **_k: messages.append(a))

    dialog.on_ok()
    assert messages and "spaces and hyphens" in messages[0][1]
    assert entry.get() == "Sternberk2"
    assert dialog.result is None
    assert entry.focused is True
    assert dialog.dialog.destroyed is False


def test_on_ok__rejects_multi_word_country(monkeypatch):
    dialog = editorial_dialog.EditorialMetadataDialog.__new__(editorial_dialog.EditorialMetadataDialog)
    entry = DummyEntry("Česká republika")
    dialog.entries = {"city": DummyEntry("Brno"), "country": entry}
    dialog.dialog = DummyDialog()
    dialog.result = None

    messages = []
    monkeypatch.setattr(editorial_dialog.messagebox, "showerror", lambda *a, **_k: messages.append(a))

    dialog.on_ok()
    assert messages and "one word" in messages[0][1]
    assert entry.get() == "Ceska republika"
    assert dialog.result is None


@pytest.mark.parametrize("typed", ["Москва", "\u0301", "東京"])
def test_on_ok__rejects_input_without_latin_letters(monkeypatch, typed):
    dialog = editorial_dialog.EditorialMetadataDialog.__new__(editorial_dialog.EditorialMetadataDialog)
    dialog.entries = {"city": DummyEntry(typed)}
    dialog.dialog = DummyDialog()
    dialog.result = None

    messages = []
    monkeypatch.setattr(editorial_dialog.messagebox, "showerror", lambda *a, **_k: messages.append(a))

    dialog.on_ok()
    assert messages and "Cyrillic" in messages[0][1]
    assert dialog.result is None


@pytest.mark.parametrize(
    "typed, expected", [("Cesky\tKrumlov", "Cesky Krumlov"), ("Usti\nnad Labem", "Usti nad Labem")]
)
def test_transliterate_to_ascii__ascii_input_only_collapses_whitespace(typed, expected):
    result = editorial_dialog.transliterate_to_ascii(typed)
    assert result == expected
    assert editorial_dialog.transliterate_to_ascii(result) == result


def test_is_valid_place_name__trailing_newline_rejected():
    assert editorial_dialog.is_valid_place_name("city", "Brno\n") is False
