"""
Unit tests for givephotobankreadymediafiles/shared/ollama_provider.py.
"""

import json
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from shared.ai_provider import ContentBlock, Message, MessageRole
from shared.ollama_provider import OllamaProvider


class DummyResponse:
    def __init__(self, status_code=200, payload=None, lines=None):
        self.status_code = status_code
        self._payload = payload or {}
        self._lines = lines or []

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("bad")

    def json(self):
        return self._payload

    def iter_lines(self):
        return self._lines


class DummySession:
    def __init__(self):
        self.get_calls = []
        self.post_calls = []
        self.responses = {}

    def get(self, url, timeout=None):
        self.get_calls.append((url, timeout))
        return self.responses.get(("GET", url), DummyResponse(status_code=404))

    def post(self, url, json=None, timeout=None, stream=False):
        self.post_calls.append((url, json, timeout, stream))
        return self.responses.get(("POST", url), DummyResponse(status_code=404))

    def close(self):
        pass


def test_convert_messages_and_options():
    provider = OllamaProvider("llava")
    provider.session = DummySession()
    messages = [
        Message.user_text("hi"),
        Message(
            role=MessageRole.USER,
            content=[
                ContentBlock.text("t"),
                ContentBlock.image_base64("AAA"),
                ContentBlock.image_url("http://img"),
            ],
        ),
    ]
    converted = provider._convert_messages_to_ollama_format(messages)
    assert converted[0]["content"] == "hi"
    assert converted[1]["content"] == "t"
    assert converted[1]["images"] == ["AAA"]

    options = provider._prepare_generation_options(num_predict=10, stop=["x"])
    assert options["num_predict"] == 10
    assert options["stop"] == ["x"]


def test_check_server_available():
    provider = OllamaProvider("llava")
    session = DummySession()
    provider.session = session
    session.responses[("GET", f"{provider.base_url}/api/tags")] = DummyResponse(status_code=200)
    assert provider._check_server_available() is True


def test_simple_and_chat_generation():
    provider = OllamaProvider("llava")
    session = DummySession()
    provider.session = session

    session.responses[("GET", f"{provider.base_url}/api/tags")] = DummyResponse(status_code=200)
    session.responses[("POST", f"{provider.base_url}/api/chat")] = DummyResponse(
        payload={
            "message": {"content": "chat"},
            "prompt_eval_count": 1,
            "eval_count": 2,
        }
    )
    session.responses[("POST", f"{provider.base_url}/api/generate")] = DummyResponse(
        payload={
            "response": "simple",
            "prompt_eval_count": 1,
            "eval_count": 1,
        }
    )

    chat_response = provider._generate_response([Message.user_text("hi"), Message.user_text("there")])
    assert chat_response.content == "chat"

    simple_response = provider._generate_response([Message.user_text("hi")])
    assert simple_response.content == "simple"


def test_streaming_generation():
    provider = OllamaProvider("llava")
    session = DummySession()
    provider.session = session

    session.responses[("GET", f"{provider.base_url}/api/tags")] = DummyResponse(status_code=200)
    chat_lines = [
        json.dumps({"message": {"content": "a"}}).encode("utf-8"),
        json.dumps({"message": {"content": "b"}, "done": True}).encode("utf-8"),
    ]
    session.responses[("POST", f"{provider.base_url}/api/chat")] = DummyResponse(lines=chat_lines)

    chunks = list(provider.generate_text_stream([Message.user_text("hi"), Message.user_text("there")]))
    assert chunks == ["a", "b"]


def test_get_available_models_and_pull():
    provider = OllamaProvider("llava")
    session = DummySession()
    provider.session = session

    session.responses[("GET", f"{provider.base_url}/api/tags")] = DummyResponse(
        status_code=200, payload={"models": [{"name": "m1"}, {"name": "m2"}]}
    )
    models = provider.get_available_models()
    assert models == ["m1", "m2"]

    pull_lines = [json.dumps({"status": "downloading"}).encode("utf-8")]
    session.responses[("POST", f"{provider.base_url}/api/pull")] = DummyResponse(lines=pull_lines)
    assert provider.pull_model("m1") is True


def test_server_unavailable_paths():
    provider = OllamaProvider("llava")
    session = DummySession()
    provider.session = session

    assert provider._check_server_available() is False
    assert provider.get_available_models() == []

    with pytest.raises(RuntimeError):
        provider._generate_response([Message.user_text("hi")])

    with pytest.raises(RuntimeError):
        list(provider.generate_text_stream([Message.user_text("hi")]))


def test_supports_images_and_model_info():
    provider = OllamaProvider("llava:7b")
    session = DummySession()
    provider.session = session
    assert provider.supports_images() is True

    session.responses[("GET", f"{provider.base_url}/api/tags")] = DummyResponse(status_code=404)
    info = provider.get_model_info()
    assert info["type"] == "ollama"
