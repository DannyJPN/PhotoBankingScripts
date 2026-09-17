"""
Unit tests for shared/user_config.py.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import shared.user_config as user_config


def test_load_from_environment(monkeypatch):
    monkeypatch.setenv("PHOTOBANK_USERNAME", "alice")
    monkeypatch.setenv("PHOTOBANK_AUTHOR", "Alice")

    config = user_config.UserConfig.__new__(user_config.UserConfig)
    result = config._load_from_environment()
    assert result["username"] == "alice"
    assert result["author"] == "Alice"


def test_load_from_file(monkeypatch, tmp_path):
    config_path = tmp_path / "user.config.json"
    config_path.write_text(json.dumps({"username": "bob", "author": "Bob"}), encoding="utf-8")

    monkeypatch.setattr(user_config.Path, "home", lambda: tmp_path / "home")
    monkeypatch.setattr(user_config.Path, "cwd", lambda: tmp_path)

    config = user_config.UserConfig.__new__(user_config.UserConfig)
    data = config._load_from_file()
    assert data["username"] == "bob"
    assert data["author"] == "Bob"


def test_getters_and_defaults(monkeypatch):
    config = user_config.UserConfig.__new__(user_config.UserConfig)
    config._config = {}
    monkeypatch.setenv("USERNAME", "system-user")

    assert config.get_username() == "system-user"
    assert config.get_author() == "Unknown Author"


def test_is_configured():
    config = user_config.UserConfig.__new__(user_config.UserConfig)
    config._config = {"author": "Custom", "location": "X"}
    assert config.is_configured() is True


def test_get_copyright_notice():
    config = user_config.UserConfig.__new__(user_config.UserConfig)
    config._config = {"author": "Me"}
    assert config.get_copyright_notice(2020) == "Me 2020"
