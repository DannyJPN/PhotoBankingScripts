"""
Unit tests for givephotobankreadymediafileslib/batch_prompts.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import batch_prompts


def test_build_batch_prompt__includes_editorial_block():
    prompt = batch_prompts.build_batch_prompt(
        "User desc",
        editorial_data={"city": "Prague", "country": "Czechia", "date": "01 01 2025"},
        categories=None,
    )

    assert "EDITORIAL REQUIREMENT" in prompt
    assert "PRAGUE, CZECHIA - 01 01 2025" in prompt


def test_build_batch_prompt__fallback_categories_block():
    prompt = batch_prompts.build_batch_prompt("Desc", editorial_data=None, categories=None)

    assert "CATEGORIES REQUIREMENTS" in prompt
    assert "- shutterstock: Select UP TO 2" in prompt
    assert "- dreamstime: Select UP TO 3" in prompt


def test_build_batch_prompt__custom_categories_block():
    prompt = batch_prompts.build_batch_prompt(
        "Desc",
        editorial_data=None,
        categories={
            "ShutterStock": ["Nature", "People"],
            "AdobeStock": ["Travel"],
            "Dreamstime": ["Food", "Sports"],
        },
    )

    assert "SHUTTERSTOCK" in prompt
    assert "Nature, People" in prompt
    assert "ADOBESTOCK" in prompt
    assert "Travel" in prompt
    assert "DREAMSTIME" in prompt
    assert "Food, Sports" in prompt


def test_build_alternative_prompt__known_tag():
    prompt = batch_prompts.build_alternative_prompt(
        "_bw",
        original_title="Title",
        original_description="Desc",
        original_keywords=["one", "two"],
        editorial=True,
    )

    assert "black and white" in prompt
    assert "This is editorial content." in prompt
    assert "keywords: one, two" in prompt.lower()


def test_build_alternative_prompt__unknown_tag():
    prompt = batch_prompts.build_alternative_prompt(
        "_custom",
        original_title="Title",
        original_description="Desc",
        original_keywords=["one"] * 12,
        editorial=False,
    )

    assert "This is commercial content." in prompt
    assert "Edit-specific instructions for _custom" in prompt
    assert "... (12 total)" in prompt
