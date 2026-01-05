"""
Security-focused tests for integrate_sorted_photos main guard rails.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "integratesortedphotos"
sys.path.insert(0, str(package_root))

import integrate_sorted_photos


def test_main_skips_copy_when_sorted_folder_missing(monkeypatch):
    args = types.SimpleNamespace(
        sortedFolder="X:/missing",
        targetFolder="X:/dest",
        log_dir="X:/logs",
        debug=False,
    )

    called = {"copy": False}

    monkeypatch.setattr(integrate_sorted_photos, "parse_arguments", lambda: args)
    monkeypatch.setattr(integrate_sorted_photos, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(integrate_sorted_photos, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(integrate_sorted_photos, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(
        integrate_sorted_photos,
        "copy_files_with_preserved_dates",
        lambda *_a, **_k: called.__setitem__("copy", True),
    )
    monkeypatch.setattr(integrate_sorted_photos.os.path, "exists", lambda _p: False)

    integrate_sorted_photos.main()
    assert called["copy"] is False
