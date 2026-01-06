"""
Integration tests for givephotobankreadymediafiles metadata generation pipeline.
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from shared.ai_provider import AIProvider, AIResponse, Message
from givephotobankreadymediafileslib.metadata_generator import MetadataGenerator


class DummyProvider(AIProvider):
    def __init__(self, responses):
        super().__init__("dummy")
        self.responses = list(responses)

    def generate_text(self, messages, **kwargs):
        content = self.responses.pop(0)
        return AIResponse(content=content, model=self.model_name)

    def generate_text_stream(self, messages, **kwargs):
        yield ""

    def create_batch_job(self, messages_list, custom_ids, **kwargs):
        raise NotImplementedError

    def get_batch_job(self, job_id):
        raise NotImplementedError

    def cancel_batch_job(self, job_id):
        return False

    def supports_images(self):
        return True


def test_generate_all_metadata_pipeline(tmp_path):
    image_path = tmp_path / "image.jpg"
    image_path.write_bytes(b"\xff\xd8\xff")

    responses = [
        json.dumps({"original": "Calm lake at sunrise"}),  # title
        json.dumps({"original": "A calm lake with warm sunrise tones."}),  # description
        json.dumps({"original": ["lake", "sunrise", "reflection"]}),  # keywords
        "Nature, Abstract",  # categories
        "YES",  # editorial
    ]
    provider = DummyProvider(responses)

    generator = MetadataGenerator(provider)
    generator.set_photobank_categories({"Shutterstock": ["Nature", "Abstract", "Other"]})

    metadata = generator.generate_all_metadata(str(image_path))

    assert metadata.title.startswith("Calm lake")
    assert "sunrise" in metadata.description.lower()
    assert "lake" in metadata.keywords
    assert metadata.categories["Shutterstock"][0] == "Nature"
    assert metadata.editorial is True
