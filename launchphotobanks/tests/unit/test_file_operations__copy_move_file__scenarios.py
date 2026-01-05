"""
Unit tests for copy_file, move_file, ensure_directory in launchphotobanks/shared/file_operations.py.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.file_operations import copy_file, move_file, ensure_directory


class TestFileOperations:
    @pytest.fixture
    def temp_dirs(self):
        src = tempfile.mkdtemp(prefix="test_file_src_")
        dest = tempfile.mkdtemp(prefix="test_file_dest_")
        yield src, dest
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(dest, ignore_errors=True)

    def test_copy_file_creates_dest_dir(self, temp_dirs):
        src, dest = temp_dirs
        src_file = Path(src, "a.txt")
        src_file.write_text("abc", encoding="utf-8")

        dest_file = Path(dest, "nested", "a.txt")
        copy_file(str(src_file), str(dest_file))

        assert dest_file.exists()
        assert dest_file.read_text(encoding="utf-8") == "abc"

    def test_copy_file_overwrite_false_skips(self, temp_dirs):
        src, dest = temp_dirs
        src_file = Path(src, "a.txt")
        dest_file = Path(dest, "a.txt")
        src_file.write_text("src", encoding="utf-8")
        dest_file.write_text("dest", encoding="utf-8")

        copy_file(str(src_file), str(dest_file), overwrite=False)
        assert dest_file.read_text(encoding="utf-8") == "dest"

    def test_copy_file_missing_source_raises(self, temp_dirs):
        src, dest = temp_dirs
        with pytest.raises(Exception):
            copy_file(str(Path(src, "missing.txt")), str(Path(dest, "missing.txt")))

    def test_move_file_creates_dest_dir(self, temp_dirs):
        src, dest = temp_dirs
        src_file = Path(src, "a.txt")
        src_file.write_text("abc", encoding="utf-8")

        dest_file = Path(dest, "nested", "a.txt")
        move_file(str(src_file), str(dest_file))

        assert dest_file.exists()
        assert not src_file.exists()

    def test_move_file_overwrite_false_skips(self, temp_dirs):
        src, dest = temp_dirs
        src_file = Path(src, "a.txt")
        dest_file = Path(dest, "a.txt")
        src_file.write_text("src", encoding="utf-8")
        dest_file.write_text("dest", encoding="utf-8")

        move_file(str(src_file), str(dest_file), overwrite=False)
        assert src_file.exists()
        assert dest_file.read_text(encoding="utf-8") == "dest"

    def test_ensure_directory(self, temp_dirs):
        _, dest = temp_dirs
        target = Path(dest, "deep", "nested")
        ensure_directory(str(target))
        assert target.exists()
