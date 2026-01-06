"""
Security-focused tests for screenshot pattern escaping.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "pullnewmediatounsorted"
sys.path.insert(0, str(package_root))

import pullnewmediatounsorted


def test_pattern_escapes_markers(monkeypatch):
    args = types.SimpleNamespace(
        raid_drive="X:/raid",
        dropbox="X:/dropbox",
        gdrive="X:/gdrive",
        onedrive_auto="X:/auto",
        onedrive_manual="X:/manual",
        snapbridge="X:/snap",
        screens_onedrive="X:/screens1",
        screens_dropbox="X:/screens2",
        account_folder="X:/account",
        target="X:/target",
        target_screen="X:/target_screen",
        final_target="X:/final",
        log_dir="X:/logs",
        debug=False,
        index_prefix="PICT",
        index_width=4,
        index_max=10,
    )

    marker = "screen(shot)+"
    monkeypatch.setattr(pullnewmediatounsorted, "SCREENSHOT_MARKERS", [marker])

    captured = {"pattern": None}

    monkeypatch.setattr(pullnewmediatounsorted, "parse_arguments", lambda: args)
    monkeypatch.setattr(pullnewmediatounsorted, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(pullnewmediatounsorted, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(pullnewmediatounsorted, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(pullnewmediatounsorted, "unify_duplicate_files", lambda *_a, **_k: None)
    monkeypatch.setattr(pullnewmediatounsorted, "replace_in_filenames", lambda *_a, **_k: None)
    monkeypatch.setattr(pullnewmediatounsorted, "normalize_indexed_filenames", lambda *_a, **_k: None)
    monkeypatch.setattr(pullnewmediatounsorted, "flatten_folder", lambda *_a, **_k: None)

    def capture_copy_folder(_src, _dest, pattern=""):
        captured["pattern"] = pattern

    monkeypatch.setattr(pullnewmediatounsorted, "copy_folder", capture_copy_folder)

    pullnewmediatounsorted.main()
    assert "\\(" in captured["pattern"]
    assert "\\+" in captured["pattern"]
