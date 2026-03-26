"""
Unit tests for list_files in launchphotobanks/shared/file_operations.py.
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

from shared.file_operations import list_files


class TestListFiles:
    @pytest.fixture
    def temp_dir(self):
        root = tempfile.mkdtemp(prefix="test_list_files_")
        nested = os.path.join(root, "nested")
        os.makedirs(nested, exist_ok=True)
        # Create files
        Path(root, "a.txt").write_text("a", encoding="utf-8")
        Path(root, "b.log").write_text("b", encoding="utf-8")
        Path(nested, "c.txt").write_text("c", encoding="utf-8")
        yield root
        shutil.rmtree(root, ignore_errors=True)

    def test_list_files_recursive(self, temp_dir):
        files = list_files(temp_dir, recursive=True)
        basenames = {os.path.basename(p) for p in files}
        assert basenames == {"a.txt", "b.log", "c.txt"}

    def test_list_files_non_recursive(self, temp_dir):
        files = list_files(temp_dir, recursive=False)
        basenames = {os.path.basename(p) for p in files}
        assert basenames == {"a.txt", "b.log"}

    def test_list_files_pattern_empty(self, temp_dir):
        files = list_files(temp_dir, pattern="")
        basenames = {os.path.basename(p) for p in files}
        assert basenames == {"a.txt", "b.log", "c.txt"}

    def test_list_files_pattern_regex(self, temp_dir):
        files = list_files(temp_dir, pattern=r"\.txt$")
        basenames = {os.path.basename(p) for p in files}
        assert basenames == {"a.txt", "c.txt"}

    def test_list_files_nonexistent_nonrecursive(self, temp_dir):
        missing = os.path.join(temp_dir, "does_not_exist")
        files = list_files(missing, recursive=False)
        assert files == []

    def test_list_files_invalid_regex(self, temp_dir):
        with pytest.raises(re.error):
            list_files(temp_dir, pattern="[")
