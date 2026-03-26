"""
Unit tests for load_csv.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

from createbatchlib.load_csv import load_csv
import createbatchlib.load_csv as load_module


class DummyTqdm:
    def __init__(self, total, desc, unit):
        self.total = total
        self.desc = desc
        self.unit = unit
        self.updates = 0

    def update(self, count):
        self.updates += count

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def patch_tqdm(monkeypatch):
    monkeypatch.setattr(load_module, "tqdm", DummyTqdm)


def test_load_csv__returns_rows_as_dicts(tmp_path, patch_tqdm):
    csv_path = tmp_path / "input.csv"
    csv_path.write_text("A,B\n1,alpha\n2,beta\n", encoding="utf-8")

    items = load_csv(str(csv_path))

    assert items == [{"A": 1, "B": "alpha"}, {"A": 2, "B": "beta"}]


def test_load_csv__missing_file_exits(patch_tqdm):
    with pytest.raises(SystemExit) as excinfo:
        load_csv("Z:/missing/file.csv")

    assert excinfo.value.code == 1
