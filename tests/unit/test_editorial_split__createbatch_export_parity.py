"""
Parity tests: createbatch and exportpreparedmedia must classify editorial content and edit types the same way,
so every media folder written by createbatch matches the CSV written by exportpreparedmedia.
"""

import importlib
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]


def load_from_script(script: str, module_names: list[str]) -> list:
    """
    Import modules of one script in isolation (each script has its own ``shared`` package).

    :param script: Script folder name, e.g. ``createbatch``.
    :param module_names: Modules to import from that script.
    :return: Imported modules in the given order.
    """
    prefixes = ("shared", "createbatchlib", "exportpreparedmedialib")
    for name in [n for n in sys.modules if n.split(".")[0] in prefixes]:
        del sys.modules[name]
    sys.path.insert(0, str(project_root / script))
    try:
        return [importlib.import_module(name) for name in module_names]
    finally:
        sys.path.remove(str(project_root / script))


cb_constants, cb_filtering, cb_media = load_from_script(
    "createbatch", ["createbatchlib.constants", "createbatchlib.filtering", "createbatchlib.media_preparation"]
)
ex_constants, ex_banks, ex_exporters = load_from_script(
    "exportpreparedmedia",
    ["exportpreparedmedialib.constants", "exportpreparedmedialib.banks_logic", "exportpreparedmedialib.exporters"],
)

TEXTS = [
    "Ostrava, Czech - 07 05 2021: Statue",
    "OSTRAVA, CZECH - 07 05 2021: Statue",
    "Frenstat pod Radhostem, Czech - 08 07 2022: Square",
    "Frydek-Mistek, Czech - 12 14 2014: Red clouds",
    "Grey shaded - Frydek-Mistek, Czech - 12 14 2014: Red clouds",
    "Frýdek-Místek, Czech - 12 14 2014: Red clouds",
    "Ostrava, Czech Republic - 07 05 2021: Statue",
    "Ostrava, Czech - 7 5 2021: Statue",
    "Yellow flower",
    "",
]

STEMS = [
    "DSC0001",
    "DSC0001_sharpen",
    "DSC0001_bw",
    "DSC0001_negative",
    "DSC0001_misty",
    "DSC0001_blurred",
    "DSC0001_sharpen_bw",
    "DSC0001_sharpen_negative",
    "DSC0001_daterem_sharpen_bw",
    "DSC0001_misty_bw",
    "bwpicture",
    "DSC0001_bw_2",
]


def test_parity__constants_match():
    assert cb_constants.EDITORIAL_REGEX == ex_constants.EDITORIAL_REGEX
    assert cb_constants.BANKS_NO_EDITORIAL == ex_constants.BANKS_NO_EDITORIAL
    assert set(cb_constants.ALTERNATIVE_EDIT_TAGS) == set(ex_constants.ALTERNATIVE_EDIT_TAGS)
    assert cb_constants.EDITORIAL_SUBFOLDER == ex_constants.EDITORIAL_OUTPUT_TAG


@pytest.mark.parametrize("text", TEXTS)
@pytest.mark.parametrize("field", ["Název", "Popis"])
def test_parity__editorial_classification(text, field):
    record = {"Název": "", "Popis": "", field: text}

    assert cb_filtering.is_editorial_record(record) == ex_banks.is_editorial_item(record)


@pytest.mark.parametrize("stem", STEMS)
def test_parity__edit_type(stem):
    subfolder = cb_media.get_edit_subfolder(stem)
    edit_type = ex_exporters.get_edit_type({"Cesta": f"J:/Foto/JPG/{stem}.jpg"})

    assert subfolder == ("original" if edit_type == "original" else f"_{edit_type}")


def test_parity__expected_editorial_detection():
    detected = [t for t in TEXTS if cb_filtering.is_editorial_record({"Název": t, "Popis": ""})]

    assert detected == [
        "Ostrava, Czech - 07 05 2021: Statue",
        "OSTRAVA, CZECH - 07 05 2021: Statue",
        "Frenstat pod Radhostem, Czech - 08 07 2022: Square",
        "Frydek-Mistek, Czech - 12 14 2014: Red clouds",
    ]
