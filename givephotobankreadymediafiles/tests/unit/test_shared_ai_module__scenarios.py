"""
Unit tests for givephotobankreadymediafiles/shared/ai_module.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

import shared.ai_module as ai_module


def test_ai_module_exports():
    for name in ai_module.__all__:
        assert hasattr(ai_module, name)


def test_ai_module_version():
    assert ai_module.__version__ == "1.0.0"
