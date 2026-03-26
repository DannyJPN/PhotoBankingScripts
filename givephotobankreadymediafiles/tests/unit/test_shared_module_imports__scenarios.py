"""
Import smoke tests for shared modules with external dependencies.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))


def test_import_ai_module():
    import shared.ai_module  # noqa: F401


def test_import_cloud_ai():
    import shared.cloud_ai  # noqa: F401


def test_import_local_ai():
    import shared.local_ai  # noqa: F401


def test_import_neural_network():
    import shared.neural_network  # noqa: F401


def test_import_openai_provider():
    import shared.openai_provider  # noqa: F401


def test_import_anthropic_provider():
    import shared.anthropic_provider  # noqa: F401


def test_import_ollama_provider():
    import shared.ollama_provider  # noqa: F401


def test_import_prompt_manager():
    import shared.prompt_manager  # noqa: F401


def test_import_config():
    import shared.config  # noqa: F401
