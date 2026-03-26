"""
Unit tests for givephotobankreadymediafileslib/metadata_generator.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import metadata_generator


class DummyProvider:
    def __init__(self, supports_images=True):
        self._supports_images = supports_images

    def supports_images(self):
        return self._supports_images


class DummyPromptManager:
    def get_character_limits(self):
        return {"title": 80, "description": 200, "keywords_max": 50}

    def get_photobank_limits(self):
        return {"shutterstock": 2}


def _make_generator():
    provider = DummyProvider()
    gen = metadata_generator.MetadataGenerator.__new__(metadata_generator.MetadataGenerator)
    gen.ai_provider = provider
    gen.prompt_manager = DummyPromptManager()
    gen.max_title_length = 80
    gen.max_description_length = 200
    gen.max_keywords = 50
    gen.photobank_categories = {}
    return gen


def test_clean_title_and_description():
    gen = _make_generator()
    assert gen._clean_title("Title: hello") == "Hello"
    assert gen._clean_description("Description: text") == "text"


def test_truncate_to_sentence__punctuation():
    gen = _make_generator()
    text = "Sentence one. Sentence two is long."
    result = gen._truncate_to_sentence(text, max_length=20)
    assert result.endswith(".")


def test_truncate_to_sentence__word_boundary():
    gen = _make_generator()
    result = gen._truncate_to_sentence("No punctuation here", max_length=10)
    assert result == "No"


def test_validate_keyword__removes_diacritics_and_symbols():
    gen = _make_generator()
    assert gen._validate_keyword("bláh-!?") == "blah"


def test_parse_keywords__dedupe():
    gen = _make_generator()
    result = gen._parse_keywords("Tree, tree, lake")
    assert result == ["Tree", "lake"]


def test_remove_duplicate_keywords__removes_multi_word():
    gen = _make_generator()
    result = gen._remove_duplicate_keywords(["blue", "pond", "blue pond"])
    assert result == ["blue", "pond"]


def test_parse_categories__limits():
    gen = _make_generator()
    available = ["Nature", "People", "Travel"]
    result = gen._parse_categories("Nature, Travel", available, "ShutterStock")
    assert result == ["Nature", "Travel"]


def test_find_best_category_match():
    gen = _make_generator()
    available = ["Nature", "People"]
    assert gen._find_best_category_match("nature", available) == "Nature"
    assert gen._find_best_category_match("peo", available) == "People"
    assert gen._find_best_category_match("other", available) is None


def test_parse_editorial_response():
    gen = _make_generator()
    assert gen._parse_editorial_response("YES - editorial") is True
    assert gen._parse_editorial_response("no") is False


def test_fallback_categories():
    gen = _make_generator()
    available = ["Other", "Nature"]
    assert gen._fallback_categories("ShutterStock", available) == ["Other"]


def test_generate_categories__unsupported_provider():
    provider = DummyProvider(supports_images=False)
    gen = metadata_generator.MetadataGenerator.__new__(metadata_generator.MetadataGenerator)
    gen.ai_provider = provider
    gen.prompt_manager = DummyPromptManager()
    gen.max_title_length = 80
    gen.max_description_length = 200
    gen.max_keywords = 50
    gen.photobank_categories = {}
    gen.set_photobank_categories({"ShutterStock": ["Other", "Nature"]})
    categories = gen.generate_categories("C:/file.jpg")
    assert categories["ShutterStock"] == ["Other"]


def test_generate_title__unsupported_provider():
    provider = DummyProvider(supports_images=False)
    gen = metadata_generator.MetadataGenerator.__new__(metadata_generator.MetadataGenerator)
    gen.ai_provider = provider
    gen.prompt_manager = DummyPromptManager()
    gen.max_title_length = 80
    gen.max_description_length = 200
    gen.max_keywords = 50
    gen.photobank_categories = {}
    try:
        gen.generate_title("C:/file.jpg")
    except ValueError as exc:
        assert "does not support image" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_create_metadata_generator__uses_factory(monkeypatch):
    called = []
    monkeypatch.setattr(metadata_generator, "create_from_model_key", lambda key, **_k: called.append(key) or DummyProvider())
    gen = metadata_generator.create_metadata_generator("provider/model")
    assert isinstance(gen, metadata_generator.MetadataGenerator)
    assert called == ["provider/model"]
