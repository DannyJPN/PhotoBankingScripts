"""
Unit tests for givephotobankreadymediafiles/shared/anthropic_provider.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from shared.ai_provider import ContentBlock, Message, MessageRole
from shared.anthropic_provider import AnthropicProvider


class DummyBlock:
    def __init__(self, text):
        self.text = text


class DummyUsage:
    def __init__(self, input_tokens, output_tokens):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class DummyResponse:
    def __init__(self):
        self.id = "resp"
        self.model = "claude-3-5-sonnet-20241022"
        self.type = "message"
        self.role = "assistant"
        self.stop_reason = "stop"
        self.usage = DummyUsage(3, 4)
        self.content = [DummyBlock("hello")]


class DummyEvent:
    def __init__(self, text):
        self.type = "content_block_delta"
        self.delta = type("delta", (), {"text": text})


class DummyStream:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        return self.events

    def __exit__(self, _exc_type, _exc, _tb):
        return False


class DummyMessages:
    def __init__(self):
        self.created = None
        self.stream_events = None

    def create(self, **kwargs):
        self.created = kwargs
        return DummyResponse()

    def stream(self, **kwargs):
        self.created = kwargs
        return DummyStream(self.stream_events)

    class batches:
        created = None
        retrieve_value = None
        results_value = None
        cancelled = []

        @classmethod
        def create(cls, **kwargs):
            cls.created = kwargs
            return type(
                "obj",
                (),
                {
                    "id": "batch1",
                    "processing_status": "in_progress",
                    "created_at": "now",
                    "type": "batch",
                    "request_counts": type("rc", (), {"__dict__": {"total": 1}})(),
                },
            )

        @classmethod
        def retrieve(cls, job_id):
            return cls.retrieve_value

        @classmethod
        def results(cls, job_id):
            return cls.results_value

        @classmethod
        def cancel(cls, job_id):
            cls.cancelled.append(job_id)


class DummyClient:
    def __init__(self):
        self.messages = DummyMessages()


def test_convert_messages_handles_system_and_images():
    provider = AnthropicProvider()
    messages = [
        Message.system("sys"),
        Message.user_text("hi"),
        Message(
            role=MessageRole.USER,
            content=[
                ContentBlock.text("t"),
                ContentBlock.image_base64("AAA", metadata={"mime_type": "image/png"}),
                ContentBlock.image_url("http://img"),
            ],
        ),
    ]
    converted = provider._convert_messages(messages)
    assert converted["system"] == "sys"
    assert converted["messages"][0]["content"] == "hi"
    assert converted["messages"][1]["content"][0]["type"] == "text"
    assert converted["messages"][1]["content"][1]["type"] == "image"


def test_make_request_and_stream():
    provider = AnthropicProvider()
    provider._client = DummyClient()
    provider._client.messages.stream_events = [DummyEvent("a"), DummyEvent("b")]

    response = provider._make_request([Message.user_text("hi")])
    assert response.content == "hello"

    chunks = list(provider._make_stream_request([Message.user_text("hi")]))
    assert chunks == ["a", "b"]


def test_create_and_get_batch_job():
    provider = AnthropicProvider()
    provider._client = DummyClient()

    job = provider.create_batch_job([[Message.user_text("hi")]], ["id1"])
    assert job.job_id == "batch1"

    provider._client.messages.batches.retrieve_value = type(
        "obj",
        (),
        {
            "processing_status": "ended",
            "created_at": "now",
            "ended_at": "done",
            "type": "batch",
            "expires_at": "later",
            "request_counts": None,
        },
    )

    result_message = type(
        "msg",
        (),
        {
            "content": [DummyBlock("ok")],
            "model": "claude-3-5-sonnet-20241022",
            "usage": DummyUsage(1, 2),
            "stop_reason": "stop",
        },
    )
    result_item = type(
        "obj",
        (),
        {
            "custom_id": "id1",
            "result": type("res", (), {"type": "succeeded", "message": result_message})(),
        },
    )
    provider._client.messages.batches.results_value = [result_item]

    job = provider.get_batch_job("batch1")
    assert job.status == "ended"
    assert job.results[0].content == "ok"


def test_cancel_batch_job():
    provider = AnthropicProvider()
    provider._client = DummyClient()
    assert provider.cancel_batch_job("job") is True


def test_cancel_batch_job_failure():
    provider = AnthropicProvider()
    provider._client = DummyClient()

    def raise_error(_job_id):
        raise RuntimeError("fail")

    provider._client.messages.batches.cancel = raise_error
    assert provider.cancel_batch_job("job") is False


def test_supports_images_and_context_limit():
    provider = AnthropicProvider(model_name="claude-3-5-sonnet-20241022")
    assert provider.supports_images() is True
    assert provider.get_context_limit() == 200_000


def test_calculate_cost_unknown_model():
    provider = AnthropicProvider(model_name="unknown")
    assert provider._calculate_cost({"input_tokens": 10, "output_tokens": 20}) == 0.0
