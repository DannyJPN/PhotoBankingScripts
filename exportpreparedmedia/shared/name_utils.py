import re
import logging
from typing import Optional, Set

# Import numbering constants from parent module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from exportpreparedmedialib.constants import (
    MIN_NUMBER_WIDTH,
    MAX_NUMBER_WIDTH,
    DEFAULT_NUMBER_WIDTH,
    MAX_NUMBER
)


def extract_numeric_suffix(filename: str, prefix: str = "PICT", width: int = DEFAULT_NUMBER_WIDTH) -> Optional[int]:
    logging.debug("Extracting numeric suffix from filename: %s, prefix=%s, width=%d", filename, prefix, width)
    # Support MIN_NUMBER_WIDTH to MAX_NUMBER_WIDTH digit numbers for flexibility
    pattern = rf"^{re.escape(prefix)}(\d{{{MIN_NUMBER_WIDTH},{MAX_NUMBER_WIDTH}}})"
    m = re.match(pattern, filename)
    if m:
        num = int(m.group(1))
        logging.debug("Extracted suffix %0*d from %s", width, num, filename)
        return num
    logging.debug("No numeric suffix in filename: %s", filename)
    return None


def generate_indexed_filename(number: int, extension: str, prefix: str = "PICT", width: int = DEFAULT_NUMBER_WIDTH) -> str:
    name = f"{prefix}{number:0{width}d}{extension}"
    logging.debug("Generated indexed filename: %s", name)
    return name


def find_next_available_number(used: Set[int], max_number: int = MAX_NUMBER) -> int:
    logging.debug("Finding next available number, used set size: %d", len(used))
    for num in range(1, max_number + 1):
        if num not in used:
            logging.debug("Next available number found: %d", num)
            return num
    error_msg = "No available numbers left"
    logging.error(error_msg)
    raise ValueError(error_msg)





