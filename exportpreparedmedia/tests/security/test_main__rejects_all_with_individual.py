"""
Security-focused tests for mutually exclusive flags.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(package_root))

import exportpreparedmedia


def test_main_rejects_all_with_individual(monkeypatch):
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
        all=True,
        include_edited=False,
        include_alternative_formats=False,
    )

    called = {"export": False}

    monkeypatch.setattr(exportpreparedmedia, "parse_arguments", lambda: args)
    monkeypatch.setattr(exportpreparedmedia, "export_to_photobanks", lambda *_a, **_k: called.__setitem__("export", True))

    exportpreparedmedia.main()
    assert called["export"] is False
