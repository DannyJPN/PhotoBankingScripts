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
        debug=False,
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
    monkeypatch.setattr(ras, "list_files", lambda *_a, **_k: [])
    monkeypatch.setattr(ras, "get_target_hash_map", lambda *_a, **_k: {})
    monkeypatch.setattr(ras, "find_duplicates", lambda *_a, **_k: {})
    monkeypatch.setattr(ras, "handle_duplicate", lambda *_a, **_k: None)

    ras.main()


def test_main__hashes_target_once_and_removes_only_confirmed_duplicates(monkeypatch, tmp_path, caplog):
    args = make_args(tmp_path)
    unsorted = tmp_path / "unsorted"
    target = tmp_path / "target"
    unsorted.mkdir()
    target.mkdir()
    (unsorted / "dup.jpg").write_bytes(b"photo")
    (unsorted / "new.jpg").write_bytes(b"new photo")
    (target / "NIK_20260612_0042.JPG").write_bytes(b"photo")

    monkeypatch.setattr(ras, "parse_arguments", lambda: args)
    monkeypatch.setattr(ras, "setup_logging", lambda **_k: None)

    import removealreadysortedoutlib.removal_operations as ops
    import shared.file_operations as fo

    hashed_folders = []
    real_map = fo.get_hash_map_from_folder

    def spy(folder, *a, **k):
        hashed_folders.append(folder)
        return real_map(folder, *a, **k)

    monkeypatch.setattr(fo, "get_hash_map_from_folder", spy)
    monkeypatch.setattr(ops, "get_hash_map_from_folder", spy)

    ras.main()

    assert hashed_folders.count(str(target)) == 1
    assert not (unsorted / "dup.jpg").exists()
    assert (unsorted / "new.jpg").exists()
    assert (target / "NIK_20260612_0042.JPG").exists()
