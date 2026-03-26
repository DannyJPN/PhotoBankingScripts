"""
Unit tests for exportpreparedmedialib/exporters.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

import exportpreparedmedialib.exporters as exporters


def test_expand_item_with_alternative_formats__missing_source(tmp_path):
    item = {"Cesta": str(tmp_path / "missing.jpg")}
    result = exporters.expand_item_with_alternative_formats(item, "Pond5", include_alternatives=True)
    assert result == []


def test_expand_item_with_alternative_formats__adds_alternative(tmp_path):
    source = tmp_path / "JPG" / "set" / "image.jpg"
    alt = tmp_path / "PNG" / "set" / "image.png"
    source.parent.mkdir(parents=True)
    alt.parent.mkdir(parents=True)
    source.write_text("x", encoding="utf-8")
    alt.write_text("y", encoding="utf-8")

    item = {"Cesta": str(source), "Soubor": source.name}
    result = exporters.expand_item_with_alternative_formats(item, "Pond5", include_alternatives=True)

    assert len(result) == 2
    assert any(r["Cesta"] == str(alt) for r in result)


def test_load_photobank_headers__decodes_delimiter(monkeypatch):
    monkeypatch.setattr(exporters, "load_csv", lambda _p: [{"bank": "X", "headers": "A,B", "delimiter": "\\t"}])

    formats = exporters.load_photobank_headers("file.csv")

    assert formats["X"]["delimiter"] == "\t"


def test_export_mediafile__missing_required_sources(monkeypatch, tmp_path):
    monkeypatch.setattr(exporters, "get_column_map", lambda _b: [{"target": "A", "source": "missing"}])
    monkeypatch.setattr(exporters, "sanitize_field", lambda v: v)

    output = tmp_path / "out.csv"
    result = exporters.export_mediafile("X", {"filename": "a.jpg"}, str(output), {})

    assert result is False


def test_export_mediafile__writes_header(monkeypatch, tmp_path):
    monkeypatch.setattr(exporters, "get_column_map", lambda _b: [{"target": "A", "source": "a"}])
    monkeypatch.setattr(exporters, "sanitize_field", lambda v: v)

    output = tmp_path / "out.csv"
    record = {"a": "1"}
    result = exporters.export_mediafile("X", record, str(output), {"X": {"delimiter": ","}})

    content = output.read_text(encoding="utf-8")
    assert result is True
    assert "A" in content


def test_export_to_photobanks__batch_split(monkeypatch, tmp_path):
    items = [{"Cesta": str(tmp_path / "a.jpg")}]
    output_paths = {"X": str(tmp_path / "out.csv")}

    monkeypatch.setattr(exporters, "load_photobank_headers", lambda _p: {"X": {"headers": "A", "delimiter": ","}})
    monkeypatch.setattr(exporters, "load_category_map", lambda *_a, **_k: {})
    monkeypatch.setattr(exporters, "load_pond_prices", lambda *_a, **_k: {})
    monkeypatch.setattr(exporters, "extract_media_properties", lambda *_a, **_k: {"filename": "a.jpg"})
    monkeypatch.setattr(exporters, "expand_item_with_alternative_formats", lambda item, bank, include_alternatives: [item])
    monkeypatch.setattr(exporters, "export_mediafile", lambda *_a, **_k: True)
    monkeypatch.setattr(exporters, "PHOTOBANK_BATCH_SIZE_LIMITS", {"X": 1})

    exporters.export_to_photobanks(items, ["X"], output_paths, filter_func=None, include_alternative_formats=False)
