"""
Unit tests for givephotobankreadymediafiles/shared/ai_provider.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from shared.ai_provider import ContentBlock, Message, MessageRole, AIProvider, AIResponse


class DummyProvider(AIProvider):
    def generate_text(self, messages, **kwargs):
        return AIResponse(content="ok", model=self.model_name)

    def generate_text_stream(self, messages, **kwargs):
        yield "ok"

    def create_batch_job(self, messages_list, custom_ids, **kwargs):
        raise NotImplementedError

    def get_batch_job(self, job_id):
        raise NotImplementedError

    def cancel_batch_job(self, job_id):
        return False


def test_content_block_text():
    block = ContentBlock.text("hello")
    assert block.type.name == "TEXT"
    assert block.content == "hello"


def test_message_factories():
    msg = Message.system("sys")
    assert msg.role == MessageRole.SYSTEM
    assert Message.user_text("hi").content == "hi"


def test_ai_provider_chat():
    provider = DummyProvider("dummy")
    assert provider.chat("hello") == "ok"
