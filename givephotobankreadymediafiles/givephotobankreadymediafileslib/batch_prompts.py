"""
Prompt templates for batch mode metadata generation.
"""
from __future__ import annotations

from typing import Optional, Dict, List


def build_batch_prompt(user_description: str, editorial_data: Optional[Dict[str, str]] = None,
                       categories: Optional[Dict[str, List[str]]] = None) -> str:
    """
    Build the batch prompt with optional editorial requirements and categories.

    Args:
        user_description: Free-form description provided by the user
        editorial_data: Optional dict with city, country, date (DD MM YYYY)
        categories: Optional dict mapping photobank names to lists of valid categories
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
                "\n"
            )

    # Build categories block with valid categories if provided
    categories_block = ""
    if categories:
        categories_block = "===== CATEGORIES REQUIREMENTS =====\n"
        categories_block += "Select appropriate categories for each photobank from the lists below.\n"
        categories_block += "Choose ONLY from the categories listed - do not invent new ones.\n\n"

        # ShutterStock
        shutterstock_cats = categories.get("ShutterStock", [])
        if shutterstock_cats:
            categories_block += "SHUTTERSTOCK (select UP TO 2):\n"
            categories_block += ", ".join(shutterstock_cats) + "\n\n"

        # AdobeStock
        adobestock_cats = categories.get("AdobeStock", [])
        if adobestock_cats:
            categories_block += "ADOBESTOCK (select UP TO 1):\n"
            categories_block += ", ".join(adobestock_cats) + "\n\n"

        # Dreamstime (lots of categories, so abbreviate)
        dreamstime_cats = categories.get("Dreamstime", [])
        if dreamstime_cats:
            categories_block += "DREAMSTIME (select UP TO 3):\n"
            # Show all categories, but they will be long
            categories_block += ", ".join(dreamstime_cats) + "\n\n"

        categories_block += "IMPORTANT:\n"
        categories_block += "- Choose categories that best match the image content and theme\n"
        categories_block += "- You don't have to select the maximum number if fewer categories are more appropriate\n\n"
    else:
        # Fallback if no categories provided
        categories_block = (
            "===== CATEGORIES REQUIREMENTS =====\n"
            "- shutterstock: Select UP TO 2 most appropriate categories\n"
            "- adobestock: Select UP TO 1 most appropriate category\n"
            "- dreamstime: Select UP TO 3 most appropriate categories\n"
            "- Choose categories that best match the image content and theme\n"
            "- You don't have to select the maximum if fewer categories are more appropriate\n\n"
        )

    return (
        "You are a professional stock photography metadata generator.\n"
        "Based on the image and the user's input below, generate complete metadata for stock photo platforms.\n"
        "\n"
        "**CRITICAL LANGUAGE REQUIREMENT**:\n"
        "- The user input below may be in Czech or other languages\n"
        "- You MUST generate ALL metadata (title, description, keywords) in ENGLISH ONLY\n"
        "- Use the user input as context to understand WHAT to describe, but ALL output must be in English\n"
        "- Never copy non-English text directly into metadata fields\n"
        "- IMPORTANT: If place names appear (cities, mountains, regions), remove all diacritics\n"
        "  Examples: 'Bílá' → 'Bila', 'Šance' → 'Sance', 'Zbojnická' → 'Zbojnicka'\n"
        "\n"
        "NOTE: User input may include descriptions, specific instructions (e.g., 'identify species', 'determine exact type'), "
        "notes about uncertainty, or contextual explanations. Interpret and apply this information appropriately.\n"
        "\n"
        "USER INPUT:\n"
        f"{user_description}\n"
        "\n"
        f"{editorial_block}"
        "===== TITLE REQUIREMENTS =====\n"
        "- **CRITICAL**: DO NOT infer information from the image filename. Analyze only the visual content.\n"
        "- Maximum 80 characters\n"
        "- Start with the main subject (e.g., \"Silhouette of Arabian horse\", \"Granite mountain landscape\", \"Woman practicing yoga\")\n"
        "- Add specific context: location, time, setting, or key characteristics\n"
        "- Be concrete and factual, not abstract or poetic\n"
        "- For nature subjects: identify specific species/types (e.g., \"spruce\" not \"tree\", \"Arabian horse\" not \"horse\", \"granite\" not \"rock\", \"monarch butterfly\" not \"butterfly\")\n"
        "- Use natural, search-friendly language\n"
        "- NO generic words like \"image\", \"photo\", \"picture\", \"beautiful\", \"stunning\"\n"
        "\n"
        "===== DESCRIPTION REQUIREMENTS =====\n"
        "- **CRITICAL**: DO NOT infer information from the image filename. Analyze only the visual content.\n"
        "- Maximum 200 characters\n"
        "- CRITICAL: Always end with complete sentences - NEVER cut off mid-sentence or mid-phrase\n"
        "- If approaching character limit, finish the current sentence and stop\n"
        "- DO NOT just copy the title - provide NEW factual details\n"
        "- Describe what you SEE in concrete, specific terms:\n"
        "  * Specific objects and their arrangement/composition\n"
        "  * For nature: specific species/types (\"Norway spruce\" not \"tree\", \"Arabian horse\" not \"horse\")\n"
        "  * Colors, textures, materials, patterns\n"
        "  * Lighting conditions (golden hour, low-light, backlit, etc.)\n"
        "  * Location details (city, region, landmark, environment type)\n"
        "  * Weather/atmospheric conditions (foggy, clear, stormy)\n"
        "  * Time indicators (sunrise, noon, evening, night)\n"
        "  * Scale and perspective (aerial view, close-up, wide angle)\n"
        "- Use natural, flowing prose that reads like complete, coherent sentences\n"
        "- Be factual and literal - describe what IS there\n"
        "\n"
        "===== KEYWORDS REQUIREMENTS =====\n"
        "- Generate ideally 50 keywords (minimum 30 if absolutely necessary)\n"
        "- STRONGLY PREFER single-word keywords (~80% of total): \"sunset\", \"mountain\", \"horse\", \"forest\"\n"
        "- Multi-word keywords ONLY when absolutely necessary (~20% of total): \"golden hour\", \"aerial view\"\n"
        "- **CRITICAL ANTI-DUPLICATION RULE**: If single words are already present (e.g., \"blue\", \"pond\"), do NOT create multi-word combinations (\"blue pond\"). Each word should appear only once.\n"
        "- For nature: Use specific species/types (\"spruce\" not \"tree\", \"Arabian\" not \"horse\", \"granite\" not \"rock\")\n"
        "- Balance: Mix ~60% specific terms, ~30% medium-broad terms, ~10% broad categories\n"
        "- Include ALL words from title and key description terms\n"
        "- Add color names if prominent: \"orange\", \"purple\", \"blue\" (as single words)\n"
        "- NO meaningless generics: \"image\", \"photo\", \"picture\", \"beautiful\", \"nice\"\n"
        "- Keywords must be lowercase where appropriate\n"
        "- Multi-word keywords must be separated by space, NEVER by hyphen\n"
        "\n"
        "Keyword hierarchy:\n"
        "1. Main subjects (specific): Objects, people, animals, landmarks visible\n"
        "2. Context (specific): Location type, environment, setting, activity\n"
        "3. Visual qualities: Colors, lighting, perspective, composition\n"
        "4. Mood/concepts: Emotions, themes clearly conveyed\n"
        "5. Technical: Photo type, season, time of day\n"
        "6. Broader categories: General terms\n"
        "\n"
        f"{categories_block}"
        "===== OUTPUT FORMAT =====\n"
        "Return ONLY valid JSON with this exact structure:\n"
        "{\n"
        "  \"title\": \"title text here\",\n"
        "  \"description\": \"description text here\",\n"
        "  \"keywords\": [\"keyword1\", \"keyword2\", \"keyword3\", ...],\n"
        "  \"categories\": {\n"
        "    \"shutterstock\": [\"Category1\", \"Category2\"],\n"
        "    \"adobestock\": [\"Category1\"],\n"
        "    \"dreamstime\": [\"Category1\", \"Category2\", \"Category3\"]\n"
        "  }\n"
        "}\n"
        "\n"
        "Return ONLY the JSON object, no other text or explanation.\n"
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
    # Map edit tags to descriptions and instructions
    edit_info = {
        "_bw": {
            "description": "black and white",
            "hint": "black and white, monochrome, or B&W",
            "title_instructions": "Add 'black and white', 'monochrome', or 'B&W' naturally at the end of the title",
            "description_instructions": "Remove all color descriptions, add phrases about monochrome aesthetic, contrast, and tonal range",
            "keywords_instructions": "Remove color keywords, add: black and white, monochrome, grayscale, bw, contrast, tones"
        },
        "_negative": {
            "description": "color negative",
            "hint": "negative, inverted colors, or color inversion",
            "title_instructions": "Add 'negative', 'inverted colors', or 'color inversion' naturally at the end",
            "description_instructions": "Adjust color descriptions for inversion, add phrases about surreal color palette and inverted tones",
            "keywords_instructions": "Adjust color keywords for inversion, add: negative, inverted, reversed colors, surreal, artistic effect"
        },
        "_sharpen": {
            "description": "sharpened",
            "hint": "sharp, detailed, crisp, or high-detail",
            "title_instructions": "Add 'sharp', 'detailed', 'crisp', or 'high-detail' naturally at the end",
            "description_instructions": "Keep all details, add phrases about enhanced sharpness, crisp details, and clarity",
            "keywords_instructions": "Keep all keywords, add: sharp, sharpened, detailed, crisp, clarity, high definition"
        },
        "_misty": {
            "description": "misty/foggy",
            "hint": "misty, foggy, hazy, or ethereal",
            "title_instructions": "Add 'misty', 'foggy', 'hazy', or 'ethereal' naturally at the end",
            "description_instructions": "Adjust visibility descriptions, add phrases about ethereal atmosphere, fog effect, and dreamy quality",
            "keywords_instructions": "Adjust clarity keywords, add: misty, foggy, hazy, fog, mist, ethereal, dreamy, atmospheric"
        },
        "_blurred": {
            "description": "blurred",
            "hint": "blurred, soft focus, or abstract",
            "title_instructions": "Add 'blurred', 'soft focus', or 'abstract' naturally at the end",
            "description_instructions": "Adjust sharpness descriptions, add phrases about soft blur effect, abstract quality, and dreamy aesthetic",
            "keywords_instructions": "Adjust or remove sharp keywords, add: blurred, blur, soft focus, gaussian blur, abstract, dreamy"
        }
    }

    edit_meta = edit_info.get(edit_tag, {
        "description": edit_tag,
        "hint": edit_tag,
        "title_instructions": f"Add '{edit_tag}' to describe this edited version",
        "description_instructions": f"Adjust description for {edit_tag} edit effect",
        "keywords_instructions": f"Add keywords related to {edit_tag} effect"
    })

    keywords_text = ", ".join(original_keywords[:10])
    if len(original_keywords) > 10:
        keywords_text += f", ... ({len(original_keywords)} total)"

    editorial_note = "This is editorial content." if editorial else "This is commercial content."

    return (
        "You are a professional stock photography metadata generator.\n"
        f"{editorial_note}\n"
        "You previously generated these metadata for the ORIGINAL image:\n"
        f"Title: \"{original_title}\"\n"
        f"Description: \"{original_description}\"\n"
        f"Keywords: {keywords_text}\n"
        "\n"
        f"Now generate metadata for the {edit_meta['description']} version of the same image.\n"
        "\n"
        "===== TITLE REQUIREMENTS =====\n"
        "- Maximum 80 characters\n"
        "- Keep the same subject and context as the original title\n"
        f"- Add '{edit_meta['hint']}' naturally to describe this edited version\n"
        "- Start with the main subject, then add the edit characteristic\n"
        "- Be concrete and factual\n"
        "- NO generic words like \"image\", \"photo\", \"picture\"\n"
        "\n"
        f"Edit-specific instructions for {edit_tag}:\n"
        f"{edit_meta['title_instructions']}\n"
        "\n"
        "===== DESCRIPTION REQUIREMENTS =====\n"
        "- Maximum 200 characters\n"
        "- Keep the same factual details as the original\n"
        f"- Adjust for the {edit_tag} edit effect as specified below\n"
        "- Use natural, flowing prose\n"
        "- Be factual and literal\n"
        "- Always end with complete sentences - NEVER cut off mid-sentence\n"
        "\n"
        f"Edit-specific adjustments for {edit_tag}:\n"
        f"{edit_meta['description_instructions']}\n"
        "\n"
        "===== KEYWORDS REQUIREMENTS =====\n"
        "- Generate ideally 50 keywords (minimum 30 if absolutely necessary)\n"
        "- Keep most keywords from the original\n"
        f"- Apply the adjustments specified below for {edit_tag}\n"
        "- PREFER single-word keywords (~80% of total)\n"
        "- Multi-word keywords only when needed, separated by space (NOT hyphen)\n"
        "- NO generic words like \"image\", \"photo\", \"picture\"\n"
        "- Keywords must be lowercase where appropriate\n"
        "- **CRITICAL ANTI-DUPLICATION RULE**: Each word should appear only once across all keywords\n"
        "\n"
        f"Edit-specific adjustments for {edit_tag}:\n"
        f"{edit_meta['keywords_instructions']}\n"
        "\n"
        "===== OUTPUT FORMAT =====\n"
        "Return ONLY valid JSON with this exact structure:\n"
        "{\n"
        "  \"title\": \"title text here\",\n"
        "  \"description\": \"description text here\",\n"
        "  \"keywords\": [\"keyword1\", \"keyword2\", \"keyword3\", ...],\n"
        "  \"categories\": {}\n"
        "}\n"
        "\n"
        "Return ONLY the JSON object, no other text or explanation.\n"
    )
