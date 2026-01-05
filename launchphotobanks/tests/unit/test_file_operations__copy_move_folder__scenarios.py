"""
Unit tests for copy_folder, move_folder, delete_folder in launchphotobanks/shared/file_operations.py.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import re
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.file_operations import copy_folder, move_folder, delete_folder


class TestFolderOperations:
    @pytest.fixture
    def folders(self):
        src = tempfile.mkdtemp(prefix="test_src_")
        dest = tempfile.mkdtemp(prefix="test_dest_")
        yield src, dest
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(dest, ignore_errors=True)

    def _make_tree(self, root: str):
        nested = os.path.join(root, "nested")
        os.makedirs(nested, exist_ok=True)
        Path(root, "a.txt").write_text("a", encoding="utf-8")
        Path(nested, "b.txt").write_text("b", encoding="utf-8")

    def test_copy_folder_basic(self, folders):
        src, dest = folders
        self._make_tree(src)

        copy_folder(src, dest, overwrite=True)

        assert os.path.exists(os.path.join(dest, "a.txt"))
        assert os.path.exists(os.path.join(dest, "nested", "b.txt"))

    def test_copy_folder_overwrite_false_noop(self, folders):
        src, dest = folders
        self._make_tree(src)
        Path(dest, "existing.txt").write_text("x", encoding="utf-8")

        copy_folder(src, dest, overwrite=False)

        assert not os.path.exists(os.path.join(dest, "a.txt"))
        assert os.path.exists(os.path.join(dest, "existing.txt"))

    def test_copy_folder_pattern_filter(self, folders):
        src, dest = folders
        self._make_tree(src)
        Path(src, "keep.log").write_text("k", encoding="utf-8")

        copy_folder(src, dest, pattern=r"\.log$")

        assert os.path.exists(os.path.join(dest, "keep.log"))
        assert not os.path.exists(os.path.join(dest, "a.txt"))

    def test_copy_folder_invalid_regex(self, folders):
        src, dest = folders
        self._make_tree(src)
        with pytest.raises(re.error):
            copy_folder(src, dest, pattern="[")

    def test_move_folder_basic(self, folders):
        src, dest = folders
        self._make_tree(src)

        move_folder(src, dest, overwrite=True)

        assert not os.path.exists(src)
        assert os.path.exists(os.path.join(dest, "a.txt"))
        assert os.path.exists(os.path.join(dest, "nested", "b.txt"))

    def test_move_folder_overwrite_false_skips(self, folders):
        src, dest = folders
        self._make_tree(src)
        Path(dest, "existing.txt").write_text("x", encoding="utf-8")

        move_folder(src, dest, overwrite=False)

        assert os.path.exists(src)
        assert os.path.exists(os.path.join(src, "a.txt"))
        assert os.path.exists(os.path.join(dest, "existing.txt"))

    def test_move_folder_empty_source_noop(self, folders):
        src, dest = folders
        move_folder(src, dest, overwrite=True)
        assert os.path.exists(src)

    def test_delete_folder(self, folders):
        src, _ = folders
        self._make_tree(src)
        delete_folder(src)
        assert not os.path.exists(src)

    def test_delete_folder_missing_raises(self):
        with pytest.raises(Exception):
            delete_folder("Z:/this/should/not/exist")
