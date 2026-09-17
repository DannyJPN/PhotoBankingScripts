"""
Unit tests for givephotobankreadymediafiles/generatealternatives.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

import generatealternatives as script


def test_parse_comma_separated():
    assert script.parse_comma_separated("a, b") == ["a", "b"]
    assert script.parse_comma_separated("") == []


def test_map_user_effects_to_tags__unknown():
    try:
        script.map_user_effects_to_tags(["unknown"])
    except ValueError as exc:
        assert "Unknown effect" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_map_user_formats_to_extensions__unknown():
    try:
        script.map_user_formats_to_extensions(["weird"])
    except ValueError as exc:
        assert "Unknown format" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_validate_file__missing(monkeypatch):
    monkeypatch.setattr(script.os.path, "exists", lambda _p: False)
    assert script.validate_file("C:/missing.jpg") is False


def test_validate_file__unsupported(monkeypatch):
    monkeypatch.setattr(script.os.path, "exists", lambda _p: True)
    assert script.validate_file("C:/file.txt") is False


def test_main__validation_failure(monkeypatch):
    args = SimpleNamespace(
        file="C:/file.jpg",
        log_dir="logs",
        debug=False,
        formats="png",
        effects="bw",
        formats_only=False,
        effects_only=False,
    )

    monkeypatch.setattr(script, "parse_arguments", lambda: args)
    monkeypatch.setattr(script, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(script, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(script, "validate_file", lambda _p: False)

    assert script.main() == 1


def test_main__nothing_to_generate(monkeypatch):
    args = SimpleNamespace(
        file="C:/file.jpg",
        log_dir="logs",
        debug=False,
        formats="",
        effects="",
        formats_only=False,
        effects_only=False,
    )

    monkeypatch.setattr(script, "parse_arguments", lambda: args)
    monkeypatch.setattr(script, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(script, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(script, "validate_file", lambda _p: True)

    assert script.main() == 1
