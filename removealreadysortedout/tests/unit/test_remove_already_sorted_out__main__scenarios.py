"""
Unit tests for remove_already_sorted_out.py.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

import remove_already_sorted_out as ras


def make_args(tmp_path, **overrides):
    defaults = dict(
        unsorted_folder=str(tmp_path / "unsorted"),
        target_folder=str(tmp_path / "target"),
        log_dir=str(tmp_path / "logs"),
        overwrite=False,
        debug=False,
        index_prefix="PICT",
        index_width=4,
        index_max=10,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_parse_arguments__defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["remove_already_sorted_out.py"])
    args = ras.parse_arguments()
    assert args.unsorted_folder


def test_main__calls_operations(monkeypatch, tmp_path):
    args = make_args(tmp_path)
    monkeypatch.setattr(ras, "parse_arguments", lambda: args)
    monkeypatch.setattr(ras, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(ras, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(ras, "setup_logging", lambda **_k: None)

    monkeypatch.setattr(ras, "remove_desktop_ini", lambda *_a, **_k: None)
    monkeypatch.setattr(ras, "unify_duplicate_files", lambda *_a, **_k: None)
    monkeypatch.setattr(ras, "replace_in_filenames", lambda *_a, **_k: None)
    monkeypatch.setattr(ras, "normalize_indexed_filenames", lambda *_a, **_k: None)
    monkeypatch.setattr(ras, "list_files", lambda *_a, **_k: [])
    monkeypatch.setattr(ras, "get_target_files_map", lambda *_a, **_k: {})
    monkeypatch.setattr(ras, "find_duplicates", lambda *_a, **_k: {})
    monkeypatch.setattr(ras, "handle_duplicate", lambda *_a, **_k: None)

    ras.main()
