"""
Unit tests for givephotobankreadymediafiles/shared/local_ai.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from shared.ai_provider import AIResponse, Message
from shared.local_ai import LocalAIProvider


class DummyLocal(LocalAIProvider):
    def __init__(self, model_name, **kwargs):
        super().__init__(model_name, **kwargs)
        self.loaded = 0
        self.unloaded = 0
        self.last_gen_kwargs = None

    def _load_model(self):
        self.loaded += 1
        self.model = "model"
        self.tokenizer = "tok"

    def _unload_model(self):
        self.unloaded += 1

    def _generate_response(self, messages, **kwargs):
        self.last_gen_kwargs = kwargs
        if messages[0].content == "bad":
            raise ValueError("bad")
        return AIResponse(
            content="ok",
            model=self.model_name,
            usage={"total_tokens": 7},
        )


def test_load_and_unload_model():
    provider = DummyLocal("dummy")
    assert provider.is_loaded is False
    provider.load_model()
    assert provider.is_loaded is True
    assert provider.loaded == 1
    provider.unload_model()
    assert provider.is_loaded is False
    assert provider.unloaded == 1
    assert provider.model is None


def test_generate_text_merges_kwargs():
    provider = DummyLocal("dummy", max_new_tokens=10, temperature=0.1)
    response = provider.generate_text([Message.user_text("hi")], top_p=0.2)
    assert response.content == "ok"
    assert provider.last_gen_kwargs["max_new_tokens"] == 10
    assert provider.last_gen_kwargs["temperature"] == 0.1
    assert provider.last_gen_kwargs["top_p"] == 0.2
    assert provider.total_generations == 1
    assert provider.total_tokens_generated == 7


def test_create_batch_job_handles_errors():
    provider = DummyLocal("dummy")
    messages_list = [
        [Message.user_text("ok")],
        [Message.user_text("bad")],
    ]
    job = provider.create_batch_job(messages_list, ["a", "b"])
    assert job.status == "completed"
    assert job.results[0].content == "ok"
    assert "Error:" in job.results[1].content


def test_local_batch_job_not_supported():
    provider = DummyLocal("dummy")
    with pytest.raises(NotImplementedError):
        provider.get_batch_job("job")
    assert provider.cancel_batch_job("job") is False


def test_supports_batch_and_usage_stats():
    provider = DummyLocal("dummy")
    assert provider.supports_batch() is True
    stats = provider.get_usage_stats()
    assert stats["model"] == "dummy"


def test_get_model_info_includes_type():
    provider = DummyLocal("dummy")
    info = provider.get_model_info()
    assert info["type"] == "local"
