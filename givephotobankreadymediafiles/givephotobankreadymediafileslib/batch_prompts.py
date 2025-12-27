"""
Prompt templates for batch mode metadata generation.
"""
from __future__ import annotations

from typing import Optional, Dict, List


def build_batch_prompt(user_description: str, editorial_data: Optional[Dict[str, str]] = None) -> str:
    """
    Build the batch prompt with optional editorial requirements.

    Args:
        user_description: Free-form description provided by the user
        editorial_data: Optional dict with city, country, date (DD MM YYYY)
    """
    editorial_block = ""
    if editorial_data:
        city = editorial_data.get("city", "").strip()
        country = editorial_data.get("country", "").strip()
        date_str = editorial_data.get("date", "").strip()
        if city and country and date_str:
            editorial_block = (
                "EDITORIAL REQUIREMENT:\n"
                f"- This is editorial content.\n"
                f"- The description MUST start with: {city.upper()}, {country.upper()} - {date_str}: \n"
            )

    return (
        "You are a professional stock photography metadata generator.\n"
        "Based on the image and the user's description, generate metadata for stock photo platforms.\n"
        "\n"
        "USER DESCRIPTION:\n"
        f"{user_description}\n"
        "\n"
        f"{editorial_block}"
        "OUTPUT JSON ONLY with this schema:\n"
        "{\n"
        "  \"title\": \"A concise, descriptive title (max 80 characters)\",\n"
        "  \"description\": \"A detailed description (max 200 characters)\",\n"
        "  \"keywords\": [\"keyword1\", \"keyword2\", \"...\"],\n"
        "  \"categories\": {\n"
        "    \"shutterstock\": [\"Primary\", \"Secondary\"],\n"
        "    \"adobestock\": [\"Single\"],\n"
        "    \"dreamstime\": [\"Category 1\", \"Category 2\", \"Category 3\"]\n"
        "  }\n"
        "}\n"
        "\n"
        "RULES:\n"
        "- All text must be in English.\n"
        "- Keywords must be relevant, unique, and lowercase if possible.\n"
        "- Avoid trademarks and brand names.\n"
        "- Use only the JSON object, no extra text.\n"
    )


def build_alternative_prompt(edit_tag: str, original_title: str, original_description: str,
                             original_keywords: List[str], editorial: bool) -> str:
    """
    Build text-only prompt for alternative metadata generation.

    Args:
        edit_tag: Alternative edit tag (e.g., _bw, _negative, _sharpen)
        original_title: Original title
        original_description: Original description
        original_keywords: Original keywords list
        editorial: Whether the original is editorial
    """
    keywords_text = ", ".join(original_keywords)
    editorial_note = "This is editorial content." if editorial else "This is commercial content."
    return (
        "You are a professional stock photography metadata generator.\n"
        f"{editorial_note}\n"
        "We already have metadata for the ORIGINAL image. Generate metadata for the EDITED version.\n"
        "\n"
        f"EDIT TYPE: {edit_tag}\n"
        f"ORIGINAL TITLE: {original_title}\n"
        f"ORIGINAL DESCRIPTION: {original_description}\n"
        f"ORIGINAL KEYWORDS: {keywords_text}\n"
        "\n"
        "OUTPUT JSON ONLY with this schema:\n"
        "{\n"
        "  \"title\": \"A concise, descriptive title (max 80 characters)\",\n"
        "  \"description\": \"A detailed description (max 200 characters)\",\n"
        "  \"keywords\": [\"keyword1\", \"keyword2\", \"...\"],\n"
        "  \"categories\": {}\n"
        "}\n"
        "\n"
        "RULES:\n"
        "- All text must be in English.\n"
        "- Focus on the edit effect in title/description.\n"
        "- Keywords must be relevant, unique, and lowercase if possible.\n"
        "- Avoid trademarks and brand names.\n"
        "- Use only the JSON object, no extra text.\n"
    )
