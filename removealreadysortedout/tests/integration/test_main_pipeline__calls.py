"""
Integration tests for remove_already_sorted_out main call flow.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

import remove_already_sorted_out


def test_main_calls_expected_steps(monkeypatch):
    args = types.SimpleNamespace(
        unsorted_folder="X:/unsorted",
        target_folder="X:/target",
        log_dir="X:/logs",
        overwrite=False,
        debug=False,
        index_prefix="PICT",
        index_width=4,
        index_max=10,
    )

    calls = {"remove_ini": 0, "unify": 0, "replace": 0, "normalize": 0, "handle": 0}

    monkeypatch.setattr(remove_already_sorted_out, "parse_arguments", lambda: args)
    monkeypatch.setattr(remove_already_sorted_out, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(remove_already_sorted_out, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(remove_already_sorted_out, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(
        remove_already_sorted_out,
        "remove_desktop_ini",
        lambda *_a, **_k: calls.__setitem__("remove_ini", calls["remove_ini"] + 1),
    )
    monkeypatch.setattr(
        remove_already_sorted_out,
        "unify_duplicate_files",
        lambda *_a, **_k: calls.__setitem__("unify", calls["unify"] + 1),
    )
    monkeypatch.setattr(
        remove_already_sorted_out,
        "replace_in_filenames",
        lambda *_a, **_k: calls.__setitem__("replace", calls["replace"] + 1),
    )
    monkeypatch.setattr(
        remove_already_sorted_out,
        "normalize_indexed_filenames",
        lambda *_a, **_k: calls.__setitem__("normalize", calls["normalize"] + 1),
    )
    monkeypatch.setattr(remove_already_sorted_out, "list_files", lambda *_a, **_k: ["a.jpg"])
    monkeypatch.setattr(remove_already_sorted_out, "get_target_files_map", lambda *_a, **_k: {"a.jpg": ["t"]})
    monkeypatch.setattr(remove_already_sorted_out, "find_duplicates", lambda *_a, **_k: {"a.jpg": ["t"]})
    monkeypatch.setattr(
        remove_already_sorted_out,
        "handle_duplicate",
        lambda *_a, **_k: calls.__setitem__("handle", calls["handle"] + 1),
    )

    remove_already_sorted_out.main()
    assert calls["remove_ini"] == 1
    assert calls["unify"] == 2
    assert calls["replace"] == 2
    assert calls["normalize"] > 0
    assert calls["handle"] == 1
