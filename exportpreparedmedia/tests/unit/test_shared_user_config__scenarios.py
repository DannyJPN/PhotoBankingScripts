"""
Unit tests for exportpreparedmedia/shared/user_config.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

import shared.user_config as user_config


def test_user_config__env_overrides(monkeypatch):
    monkeypatch.setattr(user_config, "_user_config_instance", None)
    monkeypatch.setenv("PHOTOBANK_USERNAME", "env_user")

    cfg = user_config.UserConfig()

    assert cfg.get_username() == "env_user"


def test_user_config__file_fallback(monkeypatch):
    monkeypatch.setattr(user_config, "_user_config_instance", None)

    class DummyConfig(user_config.UserConfig):
        def _load_from_file(self):
            return {"author": "File Author", "location": "File Town"}

        def _load_from_environment(self):
            return {}

    cfg = DummyConfig()

    assert cfg.get_author() == "File Author"
    assert cfg.get_location() == "File Town"


def test_user_config__is_configured(monkeypatch):
    class DummyConfig(user_config.UserConfig):
        def _load_from_file(self):
            return {}

        def _load_from_environment(self):
            return {}

        def _get_system_defaults(self):
            return {"author": "Unknown Author", "location": "Unknown Location", "username": "u", "email": ""}

    cfg = DummyConfig()

    assert cfg.is_configured() is False
