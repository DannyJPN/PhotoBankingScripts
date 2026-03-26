"""
Security-focused tests for keyword sanitization.
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


def test_validate_keyword_strips_scripts_and_symbols():
    generator = MetadataGenerator(DummyProvider())
    keyword = "<script>alert('x')</script> DROP; TABLE"
    cleaned = generator._validate_keyword(keyword)
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert ";" not in cleaned
    assert "DROP" in cleaned
