"""
Unit tests for givephotobankreadymediafiles/shared/openai_provider.py.
"""

import io
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from shared.ai_provider import ContentBlock, Message, MessageRole
from shared.openai_provider import OpenAIProvider


class DummyChoice:
    def __init__(self, content, finish_reason):
        self.message = type("msg", (), {"content": content})
        self.finish_reason = finish_reason


class DummyUsage:
    def __init__(self, prompt, completion, total):
        self.prompt_tokens = prompt
        self.completion_tokens = completion
        self.total_tokens = total


class DummyResponse:
    def __init__(self):
        self.id = "resp"
        self.model = "gpt-4o"
        self.created = 123
        self.choices = [DummyChoice("hello", "stop")]
        self.usage = DummyUsage(1, 2, 3)


class DummyCompletions:
    def __init__(self, response):
        self._response = response
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class DummyChat:
    def __init__(self, response):
        self.completions = DummyCompletions(response)


class DummyFiles:
    def __init__(self, file_id):
        self.file_id = file_id
        self.content_value = None

    def create(self, file, purpose):
        return type("obj", (), {"id": self.file_id})

    def content(self, file_id):
        return self.content_value


class DummyBatches:
    def __init__(self):
        self.created = None
        self.retrieve_value = None
        self.cancelled = []

    def create(self, **kwargs):
        self.created = kwargs
        return type(
            "obj",
            (),
            {
                "id": "batch1",
                "status": "validating",
                "created_at": 10,
                "endpoint": "/v1/chat/completions",
                "completion_window": "24h",
            },
        )

    def retrieve(self, job_id):
        return self.retrieve_value

    def cancel(self, job_id):
        self.cancelled.append(job_id)


class DummyClient:
    def __init__(self):
        self.chat = DummyChat(DummyResponse())
        self.files = DummyFiles("file1")
        self.batches = DummyBatches()


def test_convert_messages_text_and_images():
    provider = OpenAIProvider("gpt-4o")
    messages = [
        Message.user_text("hi"),
        Message(
            role=MessageRole.USER,
            content=[
                ContentBlock.text("t"),
                ContentBlock.image_url("http://img"),
                ContentBlock.image_base64("AAA", metadata={"mime_type": "image/png"}),
            ],
        ),
    ]
    converted = provider._convert_messages(messages)
    assert converted[0]["content"] == "hi"
    assert converted[1]["content"][1]["type"] == "image_url"
    assert "data:image/png;base64,AAA" in converted[1]["content"][2]["image_url"]["url"]


def test_make_request_and_supports_images(monkeypatch):
    provider = OpenAIProvider("gpt-4o")
    provider._client = DummyClient()

    response = provider._make_request([Message.user_text("hi")])
    assert response.content == "hello"

    provider.model_name = "gpt-5-nano"
    assert provider.supports_images() is False
    provider.model_name = "gpt-4o"
    assert provider.supports_images() is True


def test_calculate_cost():
    provider = OpenAIProvider("gpt-4o")
    cost = provider._calculate_cost({"prompt_tokens": 1000, "completion_tokens": 1000})
    assert cost > 0
    provider.model_name = "unknown"
    assert provider._calculate_cost({"prompt_tokens": 1000, "completion_tokens": 1000}) == 0.0


def test_create_batch_job_and_cleanup(monkeypatch, tmp_path):
    provider = OpenAIProvider("gpt-4o")
    provider._client = DummyClient()

    written = {}
    deleted = {}

    def fake_write_text(path, content):
        written["path"] = path
        written["content"] = content

    @contextmanager
    def fake_open_file_handle(path, mode):
        yield io.BytesIO(b"data")

    def fake_delete_file(path):
        deleted["path"] = path

    monkeypatch.setattr("shared.openai_provider.write_text", fake_write_text)
    monkeypatch.setattr("shared.openai_provider.open_file_handle", fake_open_file_handle)
    monkeypatch.setattr("shared.openai_provider.delete_file", fake_delete_file)

    job = provider.create_batch_job([[Message.user_text("hi")]], ["id1"])
    assert job.job_id == "batch1"
    assert "id1" in written["content"]
    assert deleted["path"]


def test_get_batch_job_parses_results():
    provider = OpenAIProvider("gpt-4o")
    provider._client = DummyClient()

    result_line = json.dumps(
        {
            "custom_id": "x",
            "response": {
                "body": {
                    "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                    "model": "gpt-4o",
                    "usage": {"total_tokens": 3},
                }
            },
        }
    )

    file_content = type(
        "obj",
        (),
        {"iter_lines": lambda self: [result_line.encode("utf-8")]},
    )()

    provider._client.files.content_value = file_content
    provider._client.batches.retrieve_value = type(
        "obj",
        (),
        {
            "status": "completed",
            "created_at": 10,
            "completed_at": 20,
            "input_file_id": "in",
            "output_file_id": "out",
            "error_file_id": None,
            "request_counts": None,
        },
    )

    job = provider.get_batch_job("job")
    assert job.status == "completed"
    assert job.results[0].content == "ok"


def test_cancel_batch_job():
    provider = OpenAIProvider("gpt-4o")
    provider._client = DummyClient()
    assert provider.cancel_batch_job("job") is True


def test_cancel_batch_job_failure():
    provider = OpenAIProvider("gpt-4o")
    client = DummyClient()

    def raise_error(_job_id):
        raise RuntimeError("fail")

    client.batches.cancel = raise_error
    provider._client = client
    assert provider.cancel_batch_job("job") is False


def test_make_stream_request():
    provider = OpenAIProvider("gpt-4o")

    class DummyDelta:
        def __init__(self, content):
            self.content = content

    class DummyChunk:
        def __init__(self, content):
            self.choices = [type("choice", (), {"delta": DummyDelta(content)})()]

    client = DummyClient()
    client.chat.completions.create = lambda **kwargs: [DummyChunk("a"), DummyChunk("b")]
    provider._client = client

    chunks = list(provider._make_stream_request([Message.user_text("hi")]))
    assert chunks == ["a", "b"]
