"""
Unit tests for givephotobankreadymediafiles/shared/cloud_ai.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from shared.ai_provider import AIResponse, Message
from shared.cloud_ai import CloudAIProvider


class DummyCloud(CloudAIProvider):
    def __init__(self, model_name, **kwargs):
        super().__init__(model_name, **kwargs)
        self.stream_chunks = []
        self.make_request_calls = 0

    def _make_request(self, messages, **kwargs):
        self.make_request_calls += 1
        return AIResponse(
            content="ok",
            model=self.model_name,
            usage={"total_tokens": 5},
            finish_reason="stop",
        )

    def _make_stream_request(self, messages, **kwargs):
        for chunk in self.stream_chunks:
            yield chunk

    def _calculate_cost(self, usage):
        return 0.1


def test_wait_for_rate_limit(monkeypatch):
    provider = DummyCloud("dummy", requests_per_minute=60)
    provider.last_request_time = 0

    times = iter([0.1, 0.1, 1.1])
    slept = {}

    def fake_time():
        return next(times)

    def fake_sleep(seconds):
        slept["value"] = seconds

    monkeypatch.setattr("shared.cloud_ai.time.time", fake_time)
    monkeypatch.setattr("shared.cloud_ai.time.sleep", fake_sleep)

    provider._wait_for_rate_limit()
    assert slept["value"] > 0
    assert provider.last_request_time == 1.1


def test_retry_on_failure(monkeypatch):
    provider = DummyCloud("dummy", max_retries=2, retry_delay=0)
    calls = {"count": 0}

    def flaky():
        calls["count"] += 1
        if calls["count"] < 3:
            raise ValueError("no")
        return "ok"

    monkeypatch.setattr("shared.cloud_ai.time.sleep", lambda _s: None)
    assert provider._retry_on_failure(flaky) == "ok"
    assert calls["count"] == 3


def test_retry_exhausted(monkeypatch):
    provider = DummyCloud("dummy", max_retries=1, retry_delay=0)

    def always_fail():
        raise RuntimeError("fail")

    monkeypatch.setattr("shared.cloud_ai.time.sleep", lambda _s: None)
    with pytest.raises(RuntimeError):
        provider._retry_on_failure(always_fail)


def test_generate_text_updates_usage(monkeypatch):
    provider = DummyCloud("dummy", requests_per_minute=1000000)
    monkeypatch.setattr("shared.cloud_ai.time.sleep", lambda _s: None)

    response = provider.generate_text([Message.user_text("hi")])
    assert response.content == "ok"
    assert provider.total_requests == 1
    assert provider.total_tokens == 5
    assert provider.total_cost == 0.1


def test_generate_text_stream():
    provider = DummyCloud("dummy")
    provider.stream_chunks = ["a", "b"]
    chunks = list(provider.generate_text_stream([Message.user_text("hi")]))
    assert chunks == ["a", "b"]


def test_reset_usage_stats():
    provider = DummyCloud("dummy")
    provider.total_requests = 5
    provider.total_tokens = 9
    provider.total_cost = 1.2
    provider.reset_usage_stats()
    assert provider.total_requests == 0
    assert provider.total_tokens == 0
    assert provider.total_cost == 0.0
