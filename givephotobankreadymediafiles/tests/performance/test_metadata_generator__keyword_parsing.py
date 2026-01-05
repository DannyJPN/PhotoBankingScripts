"""
Performance-oriented tests for metadata keyword parsing.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from shared.ai_provider import AIProvider
from givephotobankreadymediafileslib.metadata_generator import MetadataGenerator


class DummyProvider(AIProvider):
    def __init__(self):
        super().__init__("dummy")

    def generate_text(self, messages, **kwargs):
        raise NotImplementedError

    def generate_text_stream(self, messages, **kwargs):
        yield ""

    def create_batch_job(self, messages_list, custom_ids, **kwargs):
        raise NotImplementedError

    def get_batch_job(self, job_id):
        raise NotImplementedError

    def cancel_batch_job(self, job_id):
        return False


def test_parse_keywords_large_payload():
    generator = MetadataGenerator(DummyProvider())
    raw = ", ".join([f"keyword{i}" for i in range(500)])
    keywords = generator._parse_keywords(raw)
    assert len(keywords) == 500
