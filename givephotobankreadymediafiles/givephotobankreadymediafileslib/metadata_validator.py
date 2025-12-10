"""
Metadata validation and character counting.

This module handles:
- Input validation for title and description
- Character counting and limit checking
- Metadata collection from UI
- Save validation
"""

import logging
from typing import Optional, Tuple
from dataclasses import dataclass

from givephotobankreadymediafileslib.constants import (
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_KEYWORDS_COUNT
)


@dataclass
class CharacterCount:
    """
    Character count information.

    :param current: Current character count
    :param maximum: Maximum allowed characters
    :param is_over_limit: Whether count exceeds maximum
    """

    current: int
    maximum: int
    is_over_limit: bool


@dataclass
class MetadataValidation:
    """
    Metadata validation result.

    :param is_valid: Whether metadata is valid
    :param error_message: Error message if invalid
    """

    is_valid: bool
    error_message: Optional[str] = None


def count_title_characters(title: str) -> CharacterCount:
    """
    Count characters in title and check against limit.

    :param title: Title text
    :return: CharacterCount with current count and limit status
    """
    current_length = len(title)
    is_over_limit = current_length > MAX_TITLE_LENGTH

    return CharacterCount(
        current=current_length,
        maximum=MAX_TITLE_LENGTH,
        is_over_limit=is_over_limit
    )


def count_description_characters(description: str) -> CharacterCount:
    """
    Count characters in description and check against limit.

    :param description: Description text (may include whitespace)
    :return: CharacterCount with current count and limit status
    """
    # Strip to get actual content length
    current_length = len(description.strip())
    is_over_limit = current_length > MAX_DESCRIPTION_LENGTH

    return CharacterCount(
        current=current_length,
        maximum=MAX_DESCRIPTION_LENGTH,
        is_over_limit=is_over_limit
    )


def count_keywords(keywords: list) -> CharacterCount:
    """
    Count keywords and check against limit.

    :param keywords: List of keyword strings
    :return: CharacterCount with current count and limit status
    """
    current_count = len(keywords)
    is_over_limit = current_count >= MAX_KEYWORDS_COUNT

    return CharacterCount(
        current=current_count,
        maximum=MAX_KEYWORDS_COUNT,
        is_over_limit=is_over_limit
    )


def format_character_count_label(count: CharacterCount) -> str:
    """
    Format character count for display in UI label.

    :param count: CharacterCount object
    :return: Formatted string like "50/80"
    """
    return f"{count.current}/{count.maximum}"


def get_label_color(count: CharacterCount) -> str:
    """
    Get label color based on character count status.

    :param count: CharacterCount object
    :return: Color name ('red' if over limit, 'black' otherwise)
    """
    return 'red' if count.is_over_limit else 'black'


def validate_title(title: str) -> MetadataValidation:
    """
    Validate title metadata.

    :param title: Title text
    :return: MetadataValidation result
    """
    if not title.strip():
        return MetadataValidation(
            is_valid=False,
            error_message="Title is required"
        )

    count = count_title_characters(title)
    if count.is_over_limit:
        return MetadataValidation(
            is_valid=False,
            error_message=f"Title exceeds maximum length of {MAX_TITLE_LENGTH} characters"
        )

    return MetadataValidation(is_valid=True)


def validate_description(description: str) -> MetadataValidation:
    """
    Validate description metadata.

    :param description: Description text
    :return: MetadataValidation result
    """
    count = count_description_characters(description)
    if count.is_over_limit:
        return MetadataValidation(
            is_valid=False,
            error_message=f"Description exceeds maximum length of {MAX_DESCRIPTION_LENGTH} characters"
        )

    return MetadataValidation(is_valid=True)


def validate_keywords(keywords: list) -> MetadataValidation:
    """
    Validate keywords metadata.

    :param keywords: List of keyword strings
    :return: MetadataValidation result
    """
    count = count_keywords(keywords)
    if count.is_over_limit:
        return MetadataValidation(
            is_valid=False,
            error_message=f"Keywords exceed maximum count of {MAX_KEYWORDS_COUNT}"
        )

    return MetadataValidation(is_valid=True)


def validate_all_metadata(
    title: str,
    description: str,
    keywords: list
) -> MetadataValidation:
    """
    Validate all metadata fields.

    :param title: Title text
    :param description: Description text
    :param keywords: List of keyword strings
    :return: MetadataValidation result (first error encountered)
    """
    # Validate title (required)
    title_validation = validate_title(title)
    if not title_validation.is_valid:
        return title_validation

    # Validate description
    desc_validation = validate_description(description)
    if not desc_validation.is_valid:
        return desc_validation

    # Validate keywords
    keywords_validation = validate_keywords(keywords)
    if not keywords_validation.is_valid:
        return keywords_validation

    return MetadataValidation(is_valid=True)


def format_keywords_for_csv(keywords: list) -> str:
    """
    Format keywords list for CSV storage.

    :param keywords: List of keyword strings
    :return: Comma-separated keywords string
    """
    return ', '.join(keywords)


def parse_keywords_from_csv(keywords_str: str) -> list:
    """
    Parse keywords from CSV string.

    :param keywords_str: Comma-separated keywords string
    :return: List of keyword strings
    """
    if not keywords_str:
        return []

    keywords = []
    for keyword in keywords_str.split(','):
        keyword = keyword.strip()
        if keyword:
            keywords.append(keyword)

    return keywords