"""
Unit tests for collect_editorial_cities in scripts/add_editorial_tags_to_photomedia.py.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Dict, List

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
script_path = package_root / "scripts" / "add_editorial_tags_to_photomedia.py"


@pytest.fixture
def script_module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ModuleType:
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(package_root))
    import shared.logging_config

    monkeypatch.setattr(shared.logging_config, "setup_logging", lambda *_a, **_k: None)
    spec = importlib.util.spec_from_file_location("add_editorial_tags_to_photomedia_under_test", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class EmptyRegistry:
        def __init__(self) -> None:
            self.data: Dict[str, List[dict]] = {"completed_batches": []}

    monkeypatch.setattr(module, "BatchRegistry", EmptyRegistry)
    return module


def test_collect_editorial_cities__reads_prefixes_case_insensitively(
    script_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    records = [
        {script_module.COL_DESCRIPTION: "OLOMOUC, CZECH - 01 02 2020: Square"},
        {script_module.COL_DESCRIPTION: "Frydek-Mistek, Czech - 12 14 2014: Sky"},
        {script_module.COL_DESCRIPTION: "Frenstat pod Radhostem, Czech - 01 02 2020: Square"},
        {script_module.COL_DESCRIPTION: "Vienna, Austria - 01 02 2020: Opera"},
        {script_module.COL_DESCRIPTION: "Sunset over hills"},
        {script_module.COL_DESCRIPTION: ""},
    ]
    monkeypatch.setattr(script_module, "load_csv", lambda _path: records)

    cities = script_module.collect_editorial_cities("PhotoMedia.csv")

    assert cities == {"OLOMOUC", "Frydek-Mistek", "Frenstat pod Radhostem"}


def test_collect_editorial_cities__csv_error_keeps_batch_cities(
    script_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_path: str) -> List[dict]:
        raise OSError("locked")

    monkeypatch.setattr(script_module, "load_csv", fail)

    assert script_module.collect_editorial_cities("PhotoMedia.csv") == set()
