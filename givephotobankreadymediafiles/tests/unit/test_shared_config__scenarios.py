"""
Unit tests for givephotobankreadymediafiles/shared/config.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

import shared.config as config_module


def test_get_ai_api_key__env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    cfg = config_module.Config.__new__(config_module.Config)
    cfg.config_data = {}
    assert cfg.get_ai_api_key("openai") == "key"


def test_get_available_ai_models__filters_missing_keys(monkeypatch):
    cfg = config_module.Config.__new__(config_module.Config)
    cfg.config_data = {
        "ai_providers": {
            "openai": {
                "name": "OpenAI",
                "models": {"gpt": {"name": "GPT", "supports_images": True}},
                "api_key": "file_key",
            }
        }
    }
    monkeypatch.setattr(cfg, "get_ai_api_key", lambda _p: "k")
    models = cfg.get_available_ai_models()
    assert models[0]["provider"] == "openai"


def test_get_default_ai_model__fallback():
    cfg = config_module.Config.__new__(config_module.Config)
    cfg.config_data = {"defaults": {"ai_provider": "openai", "ai_model": "gpt"}}
    cfg.get_ai_model_config = lambda *_a, **_k: None
    cfg.get_available_ai_models = lambda: []
    assert cfg.get_default_ai_model() == ("openai", "gpt")
