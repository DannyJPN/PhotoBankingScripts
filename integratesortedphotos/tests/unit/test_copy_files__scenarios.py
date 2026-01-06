"""
Unit tests for integratesortedphotoslib.copy_files.copy_files_with_preserved_dates.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from integratesortedphotoslib.copy_files import copy_files_with_preserved_dates


class TestCopyFilesWithPreservedDates:
    @pytest.fixture
    def temp_dirs(self):
        src = tempfile.mkdtemp(prefix="test_copy_src_")
        dest = tempfile.mkdtemp(prefix="test_copy_dest_")
        yield src, dest
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(dest, ignore_errors=True)

    def test_copies_nested_files(self, temp_dirs):
        src, dest = temp_dirs
        nested = Path(src, "nested")
        nested.mkdir(parents=True, exist_ok=True)
        (Path(src) / "a.txt").write_text("a", encoding="utf-8")
        (nested / "b.txt").write_text("b", encoding="utf-8")

        copy_files_with_preserved_dates(src, dest)

        assert Path(dest, "a.txt").exists()
        assert Path(dest, "nested", "b.txt").exists()

    def test_skips_existing_destination(self, temp_dirs):
        src, dest = temp_dirs
        src_file = Path(src, "a.txt")
        dest_file = Path(dest, "a.txt")
        src_file.write_text("src", encoding="utf-8")
        dest_file.write_text("dest", encoding="utf-8")

        copy_files_with_preserved_dates(src, dest)

        assert dest_file.read_text(encoding="utf-8") == "dest"

    def test_empty_source_noop(self, temp_dirs):
        src, dest = temp_dirs
        copy_files_with_preserved_dates(src, dest)
        assert list(Path(dest).rglob("*")) == []

    def test_copy_failure_raises(self, temp_dirs, monkeypatch):
        src, dest = temp_dirs
        src_file = Path(src, "a.txt")
        src_file.write_text("src", encoding="utf-8")

        from integratesortedphotoslib import copy_files as module

        def _boom(*args, **kwargs):
            raise PermissionError("nope")

        monkeypatch.setattr(module, "copy_file", _boom)

        with pytest.raises(PermissionError):
            copy_files_with_preserved_dates(src, dest)
