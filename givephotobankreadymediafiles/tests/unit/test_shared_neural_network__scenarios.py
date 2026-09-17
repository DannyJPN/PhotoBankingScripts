"""
Unit tests for givephotobankreadymediafiles/shared/neural_network.py.
"""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from shared.ai_provider import AIResponse, Message
from shared.neural_network import NeuralNetworkProvider


class DummyModel:
    def __init__(self):
        self.evaluated = False

    def eval(self):
        self.evaluated = True


class DummyNN(NeuralNetworkProvider):
    def __init__(self, model_name, model_config, **kwargs):
        super().__init__(model_name, model_config, **kwargs)
        self.loaded_checkpoint = None
        self.saved_checkpoint = None

    def _build_model(self):
        return DummyModel()

    def _load_checkpoint(self, checkpoint_path):
        self.loaded_checkpoint = checkpoint_path

    def _save_checkpoint(self, checkpoint_path):
        self.saved_checkpoint = checkpoint_path

    def _preprocess_messages(self, messages):
        return {"count": len(messages)}

    def _postprocess_output(self, model_output):
        return f"processed-{model_output}"

    def _forward_pass(self, input_data, **kwargs):
        return "output"


def test_load_model_with_checkpoint(tmp_path):
    checkpoint = tmp_path / "ckpt.bin"
    checkpoint.write_text("data", encoding="utf-8")
    provider = DummyNN("dummy", {"supports_images": True}, checkpoint_path=str(checkpoint))
    provider.load_model()
    assert provider.is_loaded is True
    assert provider.loaded_checkpoint == str(checkpoint)
    assert provider.model.evaluated is True


def test_generate_text_updates_stats():
    provider = DummyNN("dummy", {}, framework="tensorflow")
    response = provider.generate_text([Message.user_text("hi")])
    assert response.content == "processed-output"
    assert provider.total_inferences == 1
    assert provider.average_inference_time > 0


def test_save_model_requires_loaded(tmp_path):
    provider = DummyNN("dummy", {})
    with pytest.raises(RuntimeError):
        provider.save_model(str(tmp_path / "model.bin"))

    provider.load_model()
    target = tmp_path / "subdir" / "model.bin"
    provider.save_model(str(target))
    assert provider.saved_checkpoint == str(target)


def test_supports_images_and_batch_job():
    provider = DummyNN("dummy", {"supports_images": False})
    assert provider.supports_images() is False
    job = provider.create_batch_job([[Message.user_text("a")]], ["id"])
    assert job.status == "completed"
    assert job.results[0].content == "processed-output"
    assert provider.supports_streaming() is False
