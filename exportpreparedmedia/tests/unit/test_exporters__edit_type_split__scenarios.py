"""
Unit tests for the per edit type / editorial split of export files in exportpreparedmedialib/exporters.py.
"""

import csv
import logging
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

import exportpreparedmedialib.exporters as exporters

EDITORIAL_TITLE = "Ostrava, Czech - 07 05 2021: Statue"


def item(name, title="Yellow flower"):
    return {"Cesta": f"J:/Foto/JPG/set/{name}", "Soubor": name, "Název": title, "Popis": ""}


@pytest.mark.parametrize(
    "name, expected",
    [
        ("DSC0001.jpg", "original"),
        ("DSC0001_sharpen.jpg", "sharpen"),
        ("DSC0001_bw.JPG", "bw"),
        ("DSC0001_sharpen_bw.jpg", "bw"),
        ("DSC0001_sharpen_negative.jpg", "negative"),
        ("DSC0001_misty.png", "misty"),
        ("DSC0001_blurred.tif", "blurred"),
        ("bwpicture.jpg", "original"),
    ],
)
def test_get_edit_type__uses_last_tag(name, expected):
    assert exporters.get_edit_type(item(name)) == expected


def test_get_edit_type__falls_back_to_soubor():
    assert exporters.get_edit_type({"Soubor": "a_negative.jpg"}) == "negative"


def test_get_group_output_file__variants(tmp_path):
    base = str(tmp_path / "CSV_Pond5.csv")

    assert exporters.get_group_output_file(base, "bw", False) == str(tmp_path / "CSV_Pond5_bw.csv")
    assert exporters.get_group_output_file(base, "original", True) == str(tmp_path / "CSV_Pond5_editorial_original.csv")
    assert exporters.get_group_output_file(base, "bw", False, 3) == str(tmp_path / "CSV_Pond5_bw_3.csv")


def test_group_records_by_edit_type__orders_by_edit_order():
    entries = [
        (item("a_bw.jpg"), {"n": 1}),
        (item("c.jpg"), {"n": 2}),
        (item("d_sharpen.jpg"), {"n": 3}),
        (item("e_bw.jpg"), {"n": 4}),
    ]

    groups = exporters.group_records_by_edit_type(entries)

    assert groups == [
        ("original", [{"n": 2}]),
        ("sharpen", [{"n": 3}]),
        ("bw", [{"n": 1}, {"n": 4}]),
    ]


def test_group_records_by_edit_type__empty():
    assert exporters.group_records_by_edit_type([]) == []


@pytest.mark.parametrize(
    "count, limit, sizes",
    [(0, 2, []), (3, 0, [3]), (3, -1, [3]), (4, 2, [2, 2]), (5, 2, [2, 2, 1])],
)
def test_split_into_batches__sizes(count, limit, sizes):
    items = [{"n": i} for i in range(count)]

    batches = exporters.split_into_batches(items, limit)

    assert [len(b) for b in batches] == sizes
    assert [x for b in batches for x in b] == items


def test_find_stale_outputs__reports_only_unwritten_edit_type_files(tmp_path):
    for name in [
        "CSV_Pond5.csv",
        "CSV_Pond5_bw.csv",
        "CSV_Pond5_misty.csv",
        "CSV_Pond5_editorial_bw_2.csv",
        "CSV_Pond5_3.csv",
        "CSV_Pond5.csv.bak_20260624",
        "CSV_Pond5_notes.csv",
        "CSV_Pond55_bw.csv",
        "CSV_Pixta_bw.csv",
    ]:
        (tmp_path / name).write_text("x", encoding="utf-8")

    stale = exporters.find_stale_outputs(str(tmp_path / "CSV_Pond5.csv"), [str(tmp_path / "CSV_Pond5_bw.csv")])

    assert [Path(p).name for p in stale] == ["CSV_Pond5_editorial_bw_2.csv", "CSV_Pond5_misty.csv"]


def test_find_stale_outputs__missing_dir(tmp_path):
    assert exporters.find_stale_outputs(str(tmp_path / "missing" / "CSV_Pond5.csv"), []) == []


@pytest.fixture
def export_env(monkeypatch):
    monkeypatch.setattr(
        exporters, "load_photobank_headers", lambda _p: {"Bank": {"headers": "Filename", "delimiter": ","}}
    )
    monkeypatch.setattr(exporters, "load_category_map", lambda *_a, **_k: {})
    monkeypatch.setattr(exporters, "load_pond_prices", lambda *_a, **_k: {})
    monkeypatch.setattr(exporters, "extract_media_properties", lambda it, *_a, **_k: {"filename": it["Soubor"]})
    monkeypatch.setattr(exporters, "expand_item_with_alternative_formats", lambda it, bank, include_alternatives: [it])
    monkeypatch.setattr(exporters, "get_column_map", lambda _b: [{"target": "Filename", "source": "filename"}])
    monkeypatch.setattr(exporters, "sanitize_field", lambda v: v)
    monkeypatch.setattr(exporters, "PHOTOBANK_BATCH_SIZE_LIMITS", {})


def read_names(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["Filename"]
    return [r[0] for r in rows[1:]]


def file_names(folder):
    return sorted(p.name for p in folder.iterdir())


def test_export_to_photobanks__writes_one_file_per_edit_type_and_editorial(export_env, tmp_path):
    items = [
        item("a.jpg"),
        item("a_bw.jpg"),
        item("b_bw.jpg"),
        item("c_negative.jpg", EDITORIAL_TITLE),
        item("d.jpg", EDITORIAL_TITLE),
    ]

    summary = exporters.export_to_photobanks(items, ["Bank"], {"Bank": str(tmp_path / "CSV_Bank.csv")})

    assert file_names(tmp_path) == [
        "CSV_Bank_bw.csv",
        "CSV_Bank_editorial_negative.csv",
        "CSV_Bank_editorial_original.csv",
        "CSV_Bank_original.csv",
    ]
    assert read_names(tmp_path / "CSV_Bank_bw.csv") == ["a_bw.jpg", "b_bw.jpg"]
    assert read_names(tmp_path / "CSV_Bank_original.csv") == ["a.jpg"]
    assert read_names(tmp_path / "CSV_Bank_editorial_negative.csv") == ["c_negative.jpg"]
    assert read_names(tmp_path / "CSV_Bank_editorial_original.csv") == ["d.jpg"]
    assert summary == {"files_written": 4, "files_failed": 0, "records_failed": 0}


def test_export_to_photobanks__batches_records_first_then_edit_types(export_env, monkeypatch, tmp_path):
    monkeypatch.setattr(exporters, "PHOTOBANK_BATCH_SIZE_LIMITS", {"Bank": 100})
    items = [item(f"o{i:03d}.jpg") for i in range(75)] + [item(f"b{i:03d}_bw.jpg") for i in range(150)]

    exporters.export_to_photobanks(items, ["Bank"], {"Bank": str(tmp_path / "CSV_Bank.csv")})

    assert file_names(tmp_path) == [
        "CSV_Bank_bw_1.csv",
        "CSV_Bank_bw_2.csv",
        "CSV_Bank_bw_3.csv",
        "CSV_Bank_original_1.csv",
    ]
    assert read_names(tmp_path / "CSV_Bank_original_1.csv") == [f"o{i:03d}.jpg" for i in range(75)]
    assert read_names(tmp_path / "CSV_Bank_bw_1.csv") == [f"b{i:03d}_bw.jpg" for i in range(25)]
    assert read_names(tmp_path / "CSV_Bank_bw_2.csv") == [f"b{i:03d}_bw.jpg" for i in range(25, 125)]
    assert read_names(tmp_path / "CSV_Bank_bw_3.csv") == [f"b{i:03d}_bw.jpg" for i in range(125, 150)]


def test_export_to_photobanks__single_batch_keeps_batch_number(export_env, monkeypatch, tmp_path):
    monkeypatch.setattr(exporters, "PHOTOBANK_BATCH_SIZE_LIMITS", {"Bank": 100})

    exporters.export_to_photobanks([item("a_bw.jpg")], ["Bank"], {"Bank": str(tmp_path / "CSV_Bank.csv")})

    assert file_names(tmp_path) == ["CSV_Bank_bw_1.csv"]


def test_export_to_photobanks__commercial_and_editorial_batches_counted_separately(export_env, monkeypatch, tmp_path):
    monkeypatch.setattr(exporters, "PHOTOBANK_BATCH_SIZE_LIMITS", {"Bank": 2})
    items = [
        item("e1.jpg", EDITORIAL_TITLE),
        item("c1.jpg"),
        item("c2.jpg"),
        item("e2_bw.jpg", EDITORIAL_TITLE),
        item("c3_bw.jpg"),
    ]

    exporters.export_to_photobanks(items, ["Bank"], {"Bank": str(tmp_path / "CSV_Bank.csv")})

    assert file_names(tmp_path) == [
        "CSV_Bank_bw_2.csv",
        "CSV_Bank_editorial_bw_1.csv",
        "CSV_Bank_editorial_original_1.csv",
        "CSV_Bank_original_1.csv",
    ]
    assert read_names(tmp_path / "CSV_Bank_original_1.csv") == ["c1.jpg", "c2.jpg"]
    assert read_names(tmp_path / "CSV_Bank_bw_2.csv") == ["c3_bw.jpg"]


def test_export_to_photobanks__alternative_formats_stay_in_batch_of_their_record(export_env, monkeypatch, tmp_path):
    monkeypatch.setattr(exporters, "PHOTOBANK_BATCH_SIZE_LIMITS", {"Bank": 1})

    def expand(it, bank, include_alternatives):
        return [it, dict(it, Soubor=it["Soubor"].replace(".jpg", ".png"))]

    monkeypatch.setattr(exporters, "expand_item_with_alternative_formats", expand)

    exporters.export_to_photobanks([item("a.jpg"), item("b.jpg")], ["Bank"], {"Bank": str(tmp_path / "CSV_Bank.csv")})

    assert read_names(tmp_path / "CSV_Bank_original_1.csv") == ["a.jpg", "a.png"]
    assert read_names(tmp_path / "CSV_Bank_original_2.csv") == ["b.jpg", "b.png"]


def test_export_to_photobanks__skips_editorial_for_bank_without_editorial(export_env, monkeypatch, tmp_path):
    monkeypatch.setattr(exporters, "should_skip_editorial", lambda it, bank: it["Název"] == EDITORIAL_TITLE)
    items = [item("a.jpg"), item("b.jpg", EDITORIAL_TITLE)]

    exporters.export_to_photobanks(items, ["Bank"], {"Bank": str(tmp_path / "CSV_Bank.csv")})

    assert file_names(tmp_path) == ["CSV_Bank_original.csv"]


def test_export_to_photobanks__warns_about_stale_files_but_not_deprecated(export_env, tmp_path, caplog):
    (tmp_path / "CSV_Bank.csv").write_text("old", encoding="utf-8")
    (tmp_path / "CSV_Bank_misty.csv").write_text("old", encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        exporters.export_to_photobanks([item("a_bw.jpg")], ["Bank"], {"Bank": str(tmp_path / "CSV_Bank.csv")})

    assert "CSV_Bank_misty.csv was not written by this export" in caplog.text
    assert "CSV_Bank.csv was not written" not in caplog.text
    assert "CSV_Bank_bw.csv was not written" not in caplog.text
    assert (tmp_path / "CSV_Bank.csv").read_text(encoding="utf-8") == "old"


def test_export_to_photobanks__summary_counts_failures(export_env, monkeypatch, tmp_path):
    monkeypatch.setattr(exporters, "export_mediafile", lambda bank, rec, out, fmts: rec["filename"] != "b_bw.jpg")
    monkeypatch.setattr(
        exporters,
        "load_photobank_headers",
        lambda _p: {"Bank": {"headers": "Filename"}, "NoHeader": {"headers": ""}},
    )
    items = [item("a.jpg"), item("b_bw.jpg")]
    paths = {"Bank": str(tmp_path / "CSV_Bank.csv"), "NoHeader": str(tmp_path / "CSV_NoHeader.csv")}

    summary = exporters.export_to_photobanks(items, ["Bank", "NoHeader"], paths)

    assert summary == {"files_written": 2, "files_failed": 2, "records_failed": 3}
    assert not (tmp_path / "CSV_NoHeader_original.csv").exists()


def test_write_batch__header_failure_returns_false(tmp_path, caplog):
    target = tmp_path / "missing_dir" / "CSV_Bank_bw.csv"

    with caplog.at_level(logging.ERROR):
        result = exporters._write_batch("Bank", [{"filename": "a.jpg"}], str(target), {"Bank": {"headers": "Filename"}})

    assert result == (False, 0)
    assert "failed to write header" in caplog.text.lower()


def test_write_batch__no_header_is_error_and_keeps_existing_file(monkeypatch, tmp_path, caplog):
    target = tmp_path / "CSV_Bank_bw.csv"
    target.write_text("previous run\n", encoding="utf-8")
    written = []
    monkeypatch.setattr(exporters, "export_mediafile", lambda bank, rec, out, fmts: written.append(rec) or True)

    with caplog.at_level(logging.ERROR):
        result = exporters._write_batch("Bank", [{"filename": "a.jpg"}], str(target), {})

    assert result == (False, 0)
    assert written == []
    assert target.read_text(encoding="utf-8") == "previous run\n"
    assert "no header defined for bank" in caplog.text.lower()


def test_write_batch__counts_exported_records(monkeypatch, tmp_path):
    monkeypatch.setattr(exporters, "export_mediafile", lambda bank, rec, out, fmts: rec["filename"] == "a.jpg")

    result = exporters._write_batch(
        "Bank", [{"filename": "a.jpg"}, {"filename": "b.jpg"}], str(tmp_path / "out.csv"), {"Bank": {"headers": "F"}}
    )

    assert result == (True, 1)
