"""
Unit tests for givephotobankreadymediafiles/shared/prompt_manager.py.
"""

import json
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from shared.prompt_manager import PromptManager, get_prompt_manager


def _write_config(path: Path):
    config = {
        "metadata_generation": {
            "title": {
                "variables": {"prefix": "Title"},
                "template": ["{prefix}", "{user_input_section}", "{context_section}"],
                "user_input_template": "User: {user_description}",
                "context_template": "Context: {context}",
            },
            "description": {
                "variables": {"prefix": "Desc"},
                "template": "{prefix}\n{user_input_section}\n{title_section}\n{context_section}",
                "user_input_template": "User: {user_description}",
                "title_template": "Title: {title}",
                "context_template": "Context: {context}",
            },
            "keywords": {
                "variables": {"prefix": "Keys"},
                "template": "{prefix}\n{title_section}\n{description_section}\nCount: {count}",
                "title_template": "Title: {title}",
                "description_template": "Description: {description}",
            },
            "categories": {
                "variables": {"prefix": "Cats"},
                "template": "{prefix} {category_word}{category_plural} {max_categories} {photobank}\n{categories_list}\n{title_section}\n{description_section}",
                "title_template": "Title: {title}",
                "description_template": "Description: {description}",
            },
            "editorial": {
                "variables": {"prefix": "Editorial"},
                "template": "{prefix}\n{title_section}\n{description_section}",
                "title_template": "Title: {title}",
                "description_template": "Description: {description}",
            },
            "title_alternative": {
                "variables": {"prefix": "AltTitle"},
                "template": "{prefix}\n{original_title}\n{edit_tag}\n{edit_instructions}",
            },
            "description_alternative": {
                "variables": {"prefix": "AltDesc"},
                "template": "{prefix}\n{original_title}\n{original_description}\n{edit_instructions}",
            },
            "keywords_alternative": {
                "variables": {"prefix": "AltKeys"},
                "template": "{prefix}\n{original_keywords}\n{count}",
            },
        },
        "character_limits": {"title": 50, "description": 100, "keywords_max": 30},
        "photobank_limits": {"adobestock": 1, "dreamstime": 3},
    }
    path.write_text(json.dumps(config), encoding="utf-8")


def test_prompt_manager_title_and_description(tmp_path):
    config_path = tmp_path / "prompts.json"
    _write_config(config_path)

    manager = PromptManager(str(config_path))
    title_prompt = manager.get_title_prompt(context="Old", user_description="Note")
    assert "Title" in title_prompt
    assert "User: Note" in title_prompt
    assert "Context: Old" in title_prompt

    description_prompt = manager.get_description_prompt(
        title="Hello", context=None, user_description="Note"
    )
    assert "Title: Hello" in description_prompt
    assert "Context:" not in description_prompt


def test_prompt_manager_keywords_and_categories(tmp_path):
    config_path = tmp_path / "prompts.json"
    _write_config(config_path)

    manager = PromptManager(str(config_path))
    keywords_prompt = manager.get_keywords_prompt(title="T", description="D", count=5)
    assert "Count: 5" in keywords_prompt

    categories_prompt = manager.get_categories_prompt(
        photobank="AdobeStock",
        categories=["A", "B"],
        title="T",
        description="D",
    )
    assert "y 1 adobestock" in categories_prompt
    assert "A, B" in categories_prompt


def test_prompt_manager_editorial_and_alternatives(tmp_path):
    config_path = tmp_path / "prompts.json"
    _write_config(config_path)

    manager = PromptManager(str(config_path))
    editorial_prompt = manager.get_editorial_prompt(title="T", description="D")
    assert "Editorial" in editorial_prompt

    title_alt = manager.get_title_alternative_prompt("_bw", "Original")
    assert "AltTitle" in title_alt

    desc_alt = manager.get_description_alternative_prompt("_bw", "Original", "Desc")
    assert "AltDesc" in desc_alt

    keywords_alt = manager.get_keywords_alternative_prompt(
        "_bw",
        "Original",
        "Desc",
        [f"k{i}" for i in range(12)],
        count=11,
    )
    assert "AltKeys" in keywords_alt
    assert "... (12 total)" in keywords_alt


def test_prompt_manager_limits_and_fallbacks(tmp_path):
    config_path = tmp_path / "missing.json"
    manager = PromptManager(str(config_path))

    title_prompt = manager.get_title_prompt()
    assert "Return ONLY the title" in title_prompt

    assert manager.get_character_limits()["title"] == 100
    assert manager.get_photobank_limits()["adobestock"] == 1


def test_prompt_manager_global_instance():
    first = get_prompt_manager()
    second = get_prompt_manager()
    assert first is second
