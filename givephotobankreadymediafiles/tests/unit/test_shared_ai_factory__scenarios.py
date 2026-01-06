"""
Unit tests for givephotobankreadymediafiles/shared/ai_factory.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

import shared.ai_factory as ai_factory


def test_get_available_models__returns_list():
    factory = ai_factory.AIFactory()
    models = factory.get_available_models(ai_factory.ProviderType.OPENAI)

    assert isinstance(models, list)
    assert "gpt-4o" in models


def test_create_from_model_selector__invalid_format():
    factory = ai_factory.AIFactory()
    with pytest.raises(ValueError):
        factory.create_from_model_selector("invalid_key")
