"""
Unit tests for unify_duplicate_files and get_hash_map_from_folder in launchphotobanks/shared/file_operations.py.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared import file_operations


class TestDedupeAndHash:
    @pytest.fixture
    def temp_dir(self):
        root = tempfile.mkdtemp(prefix="test_dedupe_")
        yield root
        shutil.rmtree(root, ignore_errors=True)

    def test_get_hash_map_empty(self, temp_dir):
        result = file_operations.get_hash_map_from_folder(temp_dir, pattern="PICT")
        assert result == {}

    def test_get_hash_map_pattern_filter(self, temp_dir, monkeypatch):
        Path(temp_dir, "PICT_1.txt").write_text("a", encoding="utf-8")
        Path(temp_dir, "OTHER.txt").write_text("b", encoding="utf-8")

        monkeypatch.setattr(file_operations, "compute_file_hash", lambda p: "hash")
        result = file_operations.get_hash_map_from_folder(temp_dir, pattern="PICT")
        assert len(result) == 1
        only_path = next(iter(result.keys()))
        assert os.path.basename(only_path) == "PICT_1.txt"

    def test_get_hash_map_hash_error_skips(self, temp_dir, monkeypatch):
        good = Path(temp_dir, "PICT_ok.txt")
        bad = Path(temp_dir, "PICT_bad.txt")
        good.write_text("a", encoding="utf-8")
        bad.write_text("b", encoding="utf-8")

        def fake_hash(path):
            if path.endswith("PICT_bad.txt"):
                raise RuntimeError("boom")
            return "hash"

        monkeypatch.setattr(file_operations, "compute_file_hash", fake_hash)
        result = file_operations.get_hash_map_from_folder(temp_dir, pattern="PICT")
        assert os.path.basename(next(iter(result.keys()))) == "PICT_ok.txt"

    def test_unify_duplicate_files_no_duplicates(self, temp_dir, monkeypatch):
        Path(temp_dir, "a.txt").write_text("a", encoding="utf-8")
        Path(temp_dir, "bbbb.txt").write_text("b", encoding="utf-8")
        monkeypatch.setattr(file_operations, "compute_file_hash", lambda p: os.path.basename(p))

        file_operations.unify_duplicate_files(temp_dir, recursive=False)
        assert set(os.listdir(temp_dir)) == {"a.txt", "bbbb.txt"}

    def test_unify_duplicate_files_renames_to_shortest(self, temp_dir, monkeypatch):
        Path(temp_dir, "aa.txt").write_text("same", encoding="utf-8")
        Path(temp_dir, "bbbb.txt").write_text("same", encoding="utf-8")
        monkeypatch.setattr(file_operations, "compute_file_hash", lambda p: "samehash")

        file_operations.unify_duplicate_files(temp_dir, recursive=False)
        names = os.listdir(temp_dir)
        assert names == ["aa.txt"]
