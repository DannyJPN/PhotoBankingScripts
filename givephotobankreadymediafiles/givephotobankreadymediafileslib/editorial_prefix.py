"""
Parsing of the editorial description prefix "City, Country - DD MM YYYY: ".
"""

import re
from typing import Dict, Optional

from givephotobankreadymediafileslib.constants import EDITORIAL_PREFIX_PATTERN


def parse_editorial_prefix(description: str) -> Optional[Dict[str, str]]:
    """
    Extract city, country and date from an editorial description prefix.

    :param description: Description that may start with "City, Country - DD MM YYYY: "
    :return: Dict with "city", "country" and "date", or None if the prefix is missing
    """
    match = re.match(EDITORIAL_PREFIX_PATTERN, description or "")
    if not match:
        return None
    return {"city": match.group(1), "country": match.group(2), "date": match.group(3)}
