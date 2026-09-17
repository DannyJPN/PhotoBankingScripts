"""
Unit tests for helper functions in givephotobankreadymediafileslib/batch_manager.py.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import batch_manager


def test_get_default_model_key(monkeypatch):
    class DummyConfig:
        def get_default_ai_model(self):
            return ("provider", "model")

    monkeypatch.setattr(batch_manager, "get_config", lambda: DummyConfig())
    assert batch_manager._get_default_model_key() == "provider/model"


def test_create_batch_provider__missing_config(monkeypatch):
    class DummyConfig:
        def get_ai_model_config(self, *_args):
            return None

    monkeypatch.setattr(batch_manager, "get_config", lambda: DummyConfig())
    try:
        batch_manager._create_batch_provider("p/m")
    except RuntimeError as exc:
        assert "No valid AI model" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")


def test_create_batch_provider__supports(monkeypatch):
    class DummyProvider:
        def supports_batch(self):
            return True

        def supports_images(self):
            return True

    class DummyConfig:
        def get_ai_model_config(self, *_args):
            return {"api_key": "key"}

    monkeypatch.setattr(batch_manager, "get_config", lambda: DummyConfig())
    monkeypatch.setattr(batch_manager, "create_from_model_key", lambda *_a, **_k: DummyProvider())

    provider = batch_manager._create_batch_provider("p/m")
    assert isinstance(provider, DummyProvider)


def test_estimate_prompt_tokens__uses_tiktoken(monkeypatch):
    class DummyEncoding:
        def encode(self, text):
            return list(text)

    class DummyToken:
        def get_encoding(self, _name):
            return DummyEncoding()

    monkeypatch.setitem(sys.modules, "tiktoken", DummyToken())
    assert batch_manager._estimate_prompt_tokens("abc") == 3


def test_estimate_vision_tokens__zero():
    assert batch_manager._estimate_vision_tokens(0, 100) == 0


def test_sanitize_text__strips_and_replaces():
    value = " a{b}\n c\r "
    assert batch_manager._sanitize_text(value) == "a(b) c"


def test_classify_send_error__message_fallback():
    assert batch_manager._classify_send_error(RuntimeError("rate limit")) == "rate_limit"
    assert batch_manager._classify_send_error(RuntimeError("auth failed")) == "auth"
    assert batch_manager._classify_send_error(RuntimeError("timeout")) == "network"


def test_get_openai_daily_count(monkeypatch):
    date_key = "2024-01-01"
    ts = int(datetime(2024, 1, 1, 12, 0).timestamp())

    class DummyBatch:
        def __init__(self, created_at):
            self.created_at = created_at

    class DummyBatches:
        def list(self, limit=200):
            return SimpleNamespace(data=[DummyBatch(ts), DummyBatch(ts)])

    class DummyClient:
        batches = DummyBatches()

    class DummyProvider:
        def _get_client(self):
            return DummyClient()

    assert batch_manager._get_openai_daily_count(DummyProvider(), date_key) == 2


def test_build_messages__missing_file(monkeypatch):
    monkeypatch.setattr(batch_manager.os.path, "exists", lambda _p: False)
    assert batch_manager._build_messages("C:/missing.jpg", "desc", None) is None


def test_build_messages__success(monkeypatch):
    monkeypatch.setattr(batch_manager.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(batch_manager, "_image_to_content_block", lambda _p: "content")
    monkeypatch.setattr(batch_manager, "build_batch_prompt", lambda *_a, **_k: "prompt")

    class DummyMessage:
        @staticmethod
        def user(content):
            return ("user", content)

    class DummyContentBlock:
        @staticmethod
        def text(text):
            return ("text", text)

    monkeypatch.setattr(batch_manager, "Message", DummyMessage)
    monkeypatch.setattr(batch_manager, "ContentBlock", DummyContentBlock)

    messages = batch_manager._build_messages("C:/file.jpg", "desc", None)
    assert messages == [("user", [("text", "prompt"), "content"])]


def test_find_record_for_path():
    records = [
        {batch_manager.COL_PATH: "C:/a.jpg"},
        {batch_manager.COL_PATH: "C:/b.jpg"},
    ]
    found = batch_manager._find_record_for_path(records, "C:\\b.jpg")
    assert found == records[1]


def test_normalize_path():
    assert "\\" not in batch_manager._normalize_path("C:\\a.jpg")


def test_build_custom_id():
    assert batch_manager._build_custom_id("C:/path/file.jpg", "batch1") == "file_batch1"


def test_parse_keywords__list_and_string():
    assert batch_manager._parse_keywords(["a", ""]) == ["a"]
    assert batch_manager._parse_keywords("a, b") == ["a", "b"]


def test_get_default_effects(monkeypatch):
    monkeypatch.setattr(batch_manager, "DEFAULT_ALTERNATIVE_EFFECTS", "bw,negative")
    monkeypatch.setattr(batch_manager, "EFFECT_NAME_MAPPING", {"bw": "_bw"})
    assert batch_manager._get_default_effects() == ["_bw", "negative"]


def test_find_or_create_alternative_batch(monkeypatch):
    class DummyRegistry:
        def __init__(self):
            self.created = False

        def get_active_batches(self, status=None):
            return {"batch_1": {"batch_type": "alternatives_bw"}} if status == "collecting" else {}

        def create_batch(self, batch_type, _size):
            self.created = True
            return "batch_new"

    registry = DummyRegistry()
    assert batch_manager._find_or_create_alternative_batch(registry, "_bw") == "batch_1"

    registry = DummyRegistry()
    registry.get_active_batches = lambda status=None: {}
    assert batch_manager._find_or_create_alternative_batch(registry, "_bw") == "batch_new"
    assert registry.created is True


def test_update_record_with_metadata__status_and_categories():
    record = {
        "ShutterStock status": batch_manager.STATUS_UNPROCESSED,
        "ShutterStock kategorie": "",
    }
    metadata = {
        "title": "Title",
        "description": "Desc",
        "keywords": ["one", "two"],
        "categories": {"ShutterStock": ["Nature"]},
    }

    batch_manager._update_record_with_metadata(record, metadata)
    assert record["ShutterStock status"] == batch_manager.STATUS_PREPARED
    assert "Nature" in record["ShutterStock kategorie"]


def test_reject_record__sets_status():
    record = {"Bank status": batch_manager.STATUS_UNPROCESSED}
    batch_manager._reject_record(record)
    assert record["Bank status"] == batch_manager.STATUS_REJECTED


def test_save_metadata_to_csv__writes(monkeypatch):
    records = [{batch_manager.COL_PATH: "C:/file.jpg", "Bank status": batch_manager.STATUS_UNPROCESSED}]
    monkeypatch.setattr(batch_manager, "load_csv", lambda _p: records)
    called = []
    monkeypatch.setattr(batch_manager, "save_csv_with_backup", lambda _r, _p: called.append(True))

    result = batch_manager._save_metadata_to_csv("media.csv", "C:/file.jpg", {"title": "t"}, False)
    assert result is True
    assert called
