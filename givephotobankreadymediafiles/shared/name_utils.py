import re
import logging
from typing import Optional, Set



def extract_numeric_suffix(filename: str, prefix: str = "PICT", width: int = 4) -> Optional[int]:
    logging.debug("Extracting numeric suffix from filename: %s, prefix=%s, width=%d", filename, prefix, width)
    pattern = rf"^{re.escape(prefix)}(\d{{{width}}})"
    m = re.match(pattern, filename)
    if m:
        num = int(m.group(1))
        logging.debug("Extracted suffix %0*d from %s", width, num, filename)
        return num
    logging.debug("No numeric suffix in filename: %s", filename)
    return None


def generate_indexed_filename(number: int, extension: str, prefix: str = "PICT", width: int = 4) -> str:
    name = f"{prefix}{number:0{width}d}{extension}"
    logging.debug("Generated indexed filename: %s", name)
    return name


def find_next_available_number(used: Set[int], max_number: int = 9999) -> int:
    logging.debug("Finding next available number, used set size: %d", len(used))
    for num in range(1, max_number + 1):
        if num not in used:
            logging.debug("Next available number found: %d", num)
            return num
    error_msg = "No available numbers left"
    logging.error(error_msg)
    raise ValueError(error_msg)





