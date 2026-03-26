"""
Integration tests for exportpreparedmedia main flow.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(package_root))

import exportpreparedmedia


def test_main_filters_edited_items(monkeypatch):
    args = types.SimpleNamespace(
        photo_csv="X:/photo.csv",
        output_dir="X:/out",
        output_prefix="CSV",
        log_dir="X:/logs",
        debug=False,
        overwrite=False,
        shutterstock=True,
        adobestock=False,
        dreamstime=False,
        depositphotos=False,
        bigstockphoto=False,
        _123rf=False,
        canstockphoto=False,
        pond5=False,
        gettyimages=False,
        alamy=False,
        all=False,
        include_edited=False,
        include_alternative_formats=False,
    )

    items = [
        {"Cesta": "C:/photos/original.jpg", "status": "kontrolovano"},
        {"Cesta": "C:/photos/upraveno/edited.jpg", "status": "kontrolovano"},
    ]

    captured = {"count": 0}

    monkeypatch.setattr(exportpreparedmedia, "parse_arguments", lambda: args)
    monkeypatch.setattr(exportpreparedmedia, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(exportpreparedmedia, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(exportpreparedmedia, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(exportpreparedmedia, "get_enabled_banks", lambda _a: ["ShutterStock"])
    monkeypatch.setattr(exportpreparedmedia, "get_output_paths", lambda *_a, **_k: {"ShutterStock": "out.csv"})
    monkeypatch.setattr(exportpreparedmedia, "load_csv", lambda _p: items)

    def fake_export(filtered_items, *_a, **_k):
        captured["count"] = len(filtered_items)

    monkeypatch.setattr(exportpreparedmedia, "export_to_photobanks", fake_export)

    exportpreparedmedia.main()
    assert captured["count"] == 1
