"""
Parsing of the editorial description prefix "City, Country - DD MM YYYY: ".

The date is only checked for the "DD MM YYYY" digit layout; its calendar validity is not verified.
"""

import logging
import re
from typing import Dict, Optional

from givephotobankreadymediafileslib.constants import EDITORIAL_PREFIX_PATTERN

EDITORIAL_PREFIX_RE = re.compile(EDITORIAL_PREFIX_PATTERN)

logger = logging.getLogger(__name__)


def parse_editorial_prefix(description: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Extract city, country and date from an editorial description prefix.

    City must be ASCII letters (words separated by a space or hyphen), country one ASCII word.
    The date is returned as written and is not validated as a calendar date.

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
        logger.debug(f"Extracted editorial data from description of {file_name}: {editorial_data}")
    else:
        logger.warning(f"Editorial file {file_name} has no 'City, Country - DD MM YYYY:' description prefix")
    return editorial_data


def has_editorial_prefix_for_city(description: Optional[str], city: str, country: str) -> bool:
    """
    Check whether a description starts with the editorial prefix of the given city and country.

    City and country are matched literally (case-insensitively), so names outside the ASCII
    grammar of :func:`parse_editorial_prefix` (e.g. with diacritics) are still recognised.

    :param description: Description to check
    :param city: Expected city (compared case-insensitively)
    :param country: Expected country (compared case-insensitively)
    :return: True if the description carries the editorial prefix of that city and country
    """
    if not description or not city or not country:
        return False
    pattern = rf"^{re.escape(city)},\s*{re.escape(country)}\s*-\s*\d{{2}}\s+\d{{2}}\s+\d{{4}}:\s*"
    return re.match(pattern, description, re.IGNORECASE) is not None
