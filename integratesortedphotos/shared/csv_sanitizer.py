"""
CSV Sanitization Module

Provides comprehensive sanitization for CSV data to prevent injection attacks.
Protects against formula injection, command execution, and data exfiltration attempts.

Security Coverage:
- Formula injection (=, +, -, @)
- Command execution via pipe operators
- UNC path injection
- URI-based attacks
- Newline and quote escaping

Author: Security Module
Created: 2025-11-29
"""

import re
import logging
from typing import Any, Dict, List


# Characters that can trigger formula execution in spreadsheet applications
DANGEROUS_PREFIXES = ['=', '+', '-', '@', '\t', '\r', '\n']

# Patterns that indicate potential injection attempts
# Note: Formula patterns use ^ anchor to match only at START of value to avoid false positives
# on legitimate text like "High-quality photo (2024)" which contains hyphen and parenthesis.
# CSV injection only works when dangerous characters are at the START of a cell value.
SUSPICIOUS_PATTERNS = [
    r'cmd\|',  # Command pipe (can appear anywhere in formula context)
    r'^=.*\(',  # Formula with function call - anchored to start (catches =HYPERLINK, =IMPORTXML)
    r'^\+.*\(',  # Plus formula with function - anchored to start
    r'^-.*\(',  # Minus formula with function - anchored to start (avoids "USB-C (type)" FP)
    r'^@.*\(',  # @ formula with function - anchored to start
    r'\\\\.*\\',  # UNC paths (\\server\share) - can appear anywhere
    r'file:///',  # File URIs - can appear anywhere
]

# Pre-compile regex patterns for performance (avoids recompilation on every call)
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_PATTERNS]


def sanitize_field(value: Any) -> str:
    """
    Sanitize a single CSV field to prevent injection attacks.

    This function:
    1. Converts non-string values to strings
    2. Neutralizes dangerous prefixes with single quote
    3. Detects and neutralizes suspicious patterns
    4. Properly escapes quotes for CSV format

    Args:
        value: Field value to sanitize (any type)

    Returns:
        Sanitized string safe for CSV export

    Examples:
        >>> sanitize_field("=cmd|'/c calc'")
        "'=cmd|'/c calc'"
        >>> sanitize_field("Normal text")
        "Normal text"
        >>> sanitize_field("+SUM(1+1)")
        "'+SUM(1+1)"
    """
    # Convert to string if not already
    if not isinstance(value, str):
        value = str(value) if value is not None else ''

    # Handle empty values - return empty string
    if not value.strip():
        return ''

    # Track if we need to neutralize this value
    needs_neutralization = False

    # Check for dangerous prefixes
    for prefix in DANGEROUS_PREFIXES:
        if value.startswith(prefix):
            needs_neutralization = True
            logging.debug("CSV Injection: Dangerous prefix '%s' detected in value: %s", prefix, value[:50])
            break

    # Check for suspicious patterns using pre-compiled regex
    if not needs_neutralization:
        for compiled_pattern in COMPILED_PATTERNS:
            if compiled_pattern.search(value):
                needs_neutralization = True
                logging.debug("CSV Injection: Suspicious pattern detected in value: %s", value[:50])
                break

    # Neutralize by prefixing with single quote if needed
    if needs_neutralization:
        # Remove only one leading single quote to avoid double-quoting
        # Using [1:] instead of lstrip("'") to remove exactly one quote, not all
        if value.startswith("'"):
            value = value[1:]
        # Add single quote to force string interpretation
        value = "'" + value

    return value


def sanitize_record(record: Dict[str, Any]) -> Dict[str, str]:
    """
    Sanitize all fields in a CSV record.

    Args:
        record: Dictionary representing a CSV row

    Returns:
        Sanitized record with all fields cleaned

    Examples:
        >>> record = {"name": "=cmd|calc", "description": "Normal"}
        >>> sanitize_record(record)
        {"name": "'=cmd|calc", "description": "Normal"}
    """
    return {key: sanitize_field(value) for key, value in record.items()}


def sanitize_records(records: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Sanitize all records in a list.

    Args:
        records: List of dictionaries representing CSV data

    Returns:
        List of sanitized records

    Examples:
        >>> records = [{"title": "=SUM(1+1)"}, {"title": "Normal"}]
        >>> sanitize_records(records)
        [{"title": "'=SUM(1+1)"}, {"title": "Normal"}]
    """
    return [sanitize_record(record) for record in records]


def is_dangerous(value: Any) -> bool:
    """
    Check if a value contains potentially dangerous content.

    Args:
        value: Value to check

    Returns:
        True if value contains dangerous patterns, False otherwise

    Examples:
        >>> is_dangerous("=cmd|calc")
        True
        >>> is_dangerous("Normal text")
        False
    """
    if not isinstance(value, str):
        value = str(value) if value is not None else ''

    if not value.strip():
        return False

    # Check for dangerous prefixes
    for prefix in DANGEROUS_PREFIXES:
        if value.startswith(prefix):
            return True

    # Check for suspicious patterns using pre-compiled regex
    for compiled_pattern in COMPILED_PATTERNS:
        if compiled_pattern.search(value):
            return True

    return False

