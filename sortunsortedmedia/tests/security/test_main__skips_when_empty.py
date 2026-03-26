"""
Security-focused tests for no-op when there are no unmatched files.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

import sortunsortedmedia


def test_main_skips_processing_when_empty(monkeypatch):
    args = types.SimpleNamespace(
        unsorted_folder="X:/unsorted",
        target_folder="X:/target",
        interval=0,
        max_parallel=1,
        debug=False,
    )

    empty = {
        "jpg_files": [],
        "other_images": [],
        "videos": [],
        "edited_images": [],
        "edited_videos": [],
    }

    called = {"process": False}

    monkeypatch.setattr(sortunsortedmedia, "parse_arguments", lambda: args)
    monkeypatch.setattr(sortunsortedmedia, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(sortunsortedmedia, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(sortunsortedmedia, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(sortunsortedmedia, "find_unmatched_media", lambda *_a, **_k: empty)
    monkeypatch.setattr(
        sortunsortedmedia,
        "process_unmatched_files",
        lambda *_a, **_k: called.__setitem__("process", True),
    )

    sortunsortedmedia.main()
    assert called["process"] is False
