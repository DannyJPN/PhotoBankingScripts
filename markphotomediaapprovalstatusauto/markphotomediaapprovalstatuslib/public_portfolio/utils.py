"""Utilities for parsing public HTML content."""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, Optional

def extract_json_ld(html: str) -> list[dict]:
    """Extract all JSON-LD blocks from an HTML page.

    :param html: Raw HTML content of the page.
    :return: List of parsed JSON-LD objects (dicts only).
    """
    blocks: list[dict] = []
    for match in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE):
        raw = match.group(1).strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                blocks.extend([item for item in data if isinstance(item, dict)])
            elif isinstance(data, dict):
                blocks.append(data)
        except json.JSONDecodeError:
            continue
    return blocks


def extract_from_json_ld(html: str) -> Dict[str, Optional[str]]:
    """Extract title, description and author from the first matching JSON-LD block.

    :param html: Raw HTML content of the page.
    :return: Dict with keys ``title``, ``description``, ``author`` (all nullable).
    """
    result: Dict[str, Optional[str]] = {
        "title": None,
        "description": None,
        "author": None,
    }
    blocks = extract_json_ld(html)
    for block in blocks:
        if not isinstance(block, dict):
            continue
        title = block.get("name")
        description = block.get("description")
        author = None
        author_block = block.get("author") or block.get("creator")
        if isinstance(author_block, dict):
            author = author_block.get("name")
        elif isinstance(author_block, list):
            for item in author_block:
                if isinstance(item, dict) and item.get("name"):
                    author = item.get("name")
                    break
        if title and not result["title"]:
            result["title"] = title
        if description and not result["description"]:
            result["description"] = description
        if author and not result["author"]:
            result["author"] = author
    return result


def extract_meta_content(html: str, name: str) -> Optional[str]:
    """Extract the ``content`` attribute of a ``<meta>`` tag by its name or property.

    :param html: Raw HTML content of the page.
    :param name: Value of the ``name`` or ``property`` attribute to search for.
    :return: Stripped content string, or ``None`` if not found.
    """
    pattern = rf"<meta[^>]+(?:property|name)=[\"']{re.escape(name)}[\"'][^>]+content=[\"']([^\"']+)[\"']"
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_title(html: str) -> Optional[str]:
    """Extract the page title from a ``<title>`` tag.

    :param html: Raw HTML content of the page.
    :return: Normalised (whitespace-collapsed) title string, or ``None`` if not found.
    """
    match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()
    return None


def build_public_asset(bank: str, url: str, contributor_id: str, title: str, description: str) -> Dict[str, str]:
    """Build a public asset dictionary from extracted metadata."""
    return {
        "bank": bank,
        "url": url,
        "contributor_id": contributor_id,
        "title": title or "",
        "description": description or "",
    }
