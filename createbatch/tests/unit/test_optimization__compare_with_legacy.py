"""
Unit tests for compare_with_legacy_approach.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

import createbatchlib.optimization as opt_module


class DummyTqdm:
    def __init__(self, iterable=None, desc=None, unit=None):
        self.iterable = iterable

    def __iter__(self):
        return iter(self.iterable or [])


def test_compare_with_legacy_approach__matches_results(monkeypatch):
    monkeypatch.setattr(opt_module, "tqdm", DummyTqdm)

    records = [
        {"Cesta": "C:/Photos/a.jpg", "Shutterstock Status": "připraveno"},
        {"Cesta": "C:/Photos/b.jpg", "Adobe Stock Status": "připraveno"},
        {"Cesta": "C:/Photos/upraven‚/c.jpg", "Shutterstock Status": "připraveno"},
    ]

    optimized, legacy = opt_module.compare_with_legacy_approach(
        records,
        status_keyword="status",
        prepared_value="připraveno",
        include_edited=False,
    )

    assert optimized == legacy
    assert set(optimized.keys()) == {"AdobeStock", "Shutterstock"}
