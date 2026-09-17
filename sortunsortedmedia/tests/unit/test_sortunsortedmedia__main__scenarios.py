"""
Unit tests for sortunsortedmedia.py.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

import sortunsortedmedia as sumedia


def make_args(tmp_path, **overrides):
    defaults = dict(
        unsorted_folder=str(tmp_path / "unsorted"),
        target_folder=str(tmp_path / "target"),
        interval=0,
        max_parallel=1,
        debug=False,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_parse_arguments__defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["sortunsortedmedia.py"])
    args = sumedia.parse_arguments()
    assert args.unsorted_folder


def test_main__no_unmatched(monkeypatch, tmp_path):
    args = make_args(tmp_path)
    monkeypatch.setattr(sumedia, "parse_arguments", lambda: args)
    monkeypatch.setattr(sumedia, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(sumedia, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(sumedia, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(sumedia, "find_unmatched_media", lambda *_a, **_k: {
        "jpg_files": [], "other_images": [], "videos": [], "edited_images": [], "edited_videos": []
    })

    assert sumedia.main() is None
