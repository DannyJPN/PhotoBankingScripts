"""
Parsing of the editorial description prefix "City, Country - DD MM YYYY: ".
"""

import logging
import re
from typing import Dict, Optional

from givephotobankreadymediafileslib.constants import EDITORIAL_PREFIX_PATTERN

EDITORIAL_PREFIX_RE = re.compile(EDITORIAL_PREFIX_PATTERN)


def parse_editorial_prefix(description: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Extract city, country and date from an editorial description prefix.

    :param description: Description that may start with "City, Country - DD MM YYYY: "
    :return: Dict with "city", "country" and "date", or None if the prefix is missing
    """
    match = EDITORIAL_PREFIX_RE.match(description or "")
    if not match:
        return None
    return {"city": match.group(1), "country": match.group(2), "date": match.group(3)}


def extract_editorial_data(description: str, file_name: str) -> Optional[Dict[str, str]]:
    """
    Parse the editorial prefix of an editorial original and log a warning when it is missing.

    :param description: Description of the editorial original
    :param file_name: File name of the original, used in log messages
    :return: Parsed editorial data, or None if the description has no editorial prefix
    """
    editorial_data = parse_editorial_prefix(description)
    if editorial_data:
        logging.debug(f"Extracted editorial data from description of {file_name}: {editorial_data}")
    else:
        logging.warning(f"Editorial file {file_name} has no 'City, Country - DD MM YYYY:' description prefix")
    return editorial_data


def has_editorial_prefix_for_city(description: Optional[str], city: str, country: str) -> bool:
    """
    Check whether a description starts with the editorial prefix of the given city and country.

    :param description: Description to check
    :param city: Expected city (compared case-insensitively)
    :param country: Expected country (compared case-insensitively)
    :return: True if the description carries the editorial prefix of that city and country
    """
    parsed = parse_editorial_prefix(description)
    if not parsed:
        return False
    return parsed["city"].lower() == city.lower() and parsed["country"].lower() == country.lower()
