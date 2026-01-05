"""
Unit tests for exportpreparedmedialib/export_objects.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

import exportpreparedmedialib.export_objects as export_objects


def test_base_export__to_dict_maps_headers(monkeypatch):
    monkeypatch.setattr(
        export_objects,
        "HEADER_MAPPINGS",
        {"ShutterStock": {"title": "Title"}},
    )

    exp = export_objects.BaseExport("ShutterStock", title="T", other="X")
    result = exp.to_dict()

    assert result["Title"] == "T"
    assert result["other"] == "X"


def test_subclasses__photobank_name():
    assert export_objects.ShutterStockExport().photobank == "ShutterStock"
    assert export_objects.AdobeStockExport().photobank == "AdobeStock"
    assert export_objects.DreamstimeExport().photobank == "Dreamstime"
    assert export_objects.DepositPhotosExport().photobank == "DepositPhotos"
    assert export_objects.BigStockPhotoExport().photobank == "BigStockPhoto"
    assert export_objects.RF123Export().photobank == "123RF"
    assert export_objects.CanStockPhotoExport().photobank == "CanStockPhoto"
    assert export_objects.Pond5Export().photobank == "Pond5"
    assert export_objects.AlamyExport().photobank == "Alamy"
    assert export_objects.GettyImagesExport().photobank == "GettyImages"
