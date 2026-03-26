"""
Unit tests for load_csv and save_csv in launchphotobanks/shared/file_operations.py.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import builtins
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.file_operations import load_csv, save_csv


class TestCsvIO:
    @pytest.fixture
    def temp_dir(self):
        root = tempfile.mkdtemp(prefix="test_csv_io_")
        yield root
        shutil.rmtree(root, ignore_errors=True)

    def test_load_csv_basic(self, temp_dir):
        csv_path = Path(temp_dir, "data.csv")
        csv_path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8-sig")

        records = load_csv(str(csv_path))
        assert records == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]

    def test_load_csv_custom_delimiter(self, temp_dir):
        csv_path = Path(temp_dir, "data.csv")
        csv_path.write_text("a;b\n1;2\n", encoding="utf-8-sig")

        records = load_csv(str(csv_path), delimiter=";")
        assert records == [{"a": "1", "b": "2"}]

    def test_load_csv_header_only(self, temp_dir):
        csv_path = Path(temp_dir, "data.csv")
        csv_path.write_text("a,b\n", encoding="utf-8-sig")

        records = load_csv(str(csv_path))
        assert records == []

    def test_load_csv_invalid_encoding(self, temp_dir):
        csv_path = Path(temp_dir, "data.csv")
        csv_path.write_text("a,b\n1,2\n", encoding="utf-8-sig")

        with pytest.raises(Exception):
            load_csv(str(csv_path), encoding="invalid-encoding")

    def test_save_csv_basic(self, temp_dir):
        csv_path = Path(temp_dir, "out.csv")
        records = [{"a": "1", "b": "2"}]

        save_csv(records, str(csv_path))
        assert csv_path.exists()
        content = csv_path.read_text(encoding="utf-8-sig")
        assert "a,b" in content

    def test_save_csv_empty_records_no_file(self, temp_dir):
        csv_path = Path(temp_dir, "out.csv")
        save_csv([], str(csv_path))
        assert not csv_path.exists()

    def test_save_csv_open_error(self, temp_dir, monkeypatch):
        csv_path = Path(temp_dir, "out.csv")
        records = [{"a": "1", "b": "2"}]

        def _raise(*args, **kwargs):
            raise PermissionError("nope")

        monkeypatch.setattr(builtins, "open", _raise)
        with pytest.raises(PermissionError):
            save_csv(records, str(csv_path))
