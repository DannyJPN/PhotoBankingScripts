"""
Integration tests for sortunsortedmedia main category ordering.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

import sortunsortedmedia


def test_main_processes_categories_in_order(monkeypatch):
    args = types.SimpleNamespace(
        unsorted_folder="X:/unsorted",
        target_folder="X:/target",
        interval=0,
        max_parallel=1,
        debug=False,
    )

    unmatched = {
        "jpg_files": ["a.jpg"],
        "other_images": ["b.png"],
        "videos": [],
        "edited_images": ["c.jpg"],
        "edited_videos": ["d.mp4"],
    }

    calls = []

    monkeypatch.setattr(sortunsortedmedia, "parse_arguments", lambda: args)
    monkeypatch.setattr(sortunsortedmedia, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(sortunsortedmedia, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(sortunsortedmedia, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(sortunsortedmedia, "find_unmatched_media", lambda *_a, **_k: unmatched)

    def fake_process(files, *_a, **_k):
        calls.append(list(files))

    monkeypatch.setattr(sortunsortedmedia, "process_unmatched_files", fake_process)

    sortunsortedmedia.main()
    assert calls == [["a.jpg"], ["b.png"], ["c.jpg"], ["d.mp4"]]
