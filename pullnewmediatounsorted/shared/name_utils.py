import re
import logging
from typing import Optional, Set, Tuple

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pullnewmediatounsortedlib.constants import (
    DATE_FORMAT,
    CAMERA_SEQ_WIDTH,
    MIN_NUMBER_WIDTH,
    MAX_NUMBER_WIDTH,
)


def extract_camera_number(filename: str, prefix: str = "PICT") -> Optional[int]:
    """
    Extract the camera sequence number from a legacy filename (e.g. NIK_8888.JPG).
    Accepts 4-6 digits to handle files that may have been assigned wider numbers by
    earlier script versions; the canonical camera counter is exactly 4 digits (0001-9999).
    """
    pattern = rf"^{re.escape(prefix)}(\d{{{MIN_NUMBER_WIDTH},{MAX_NUMBER_WIDTH}}})\."
    m = re.match(pattern, filename, re.IGNORECASE)
    if m:
        num = int(m.group(1))
        logging.debug("Extracted camera number %d from %s", num, filename)
        return num
    logging.debug("No camera number found in %s", filename)
    return None


def extract_dated_parts(filename: str, prefix: str = "PICT") -> Optional[Tuple[str, int]]:
    """
    Parse a dated filename (e.g. NIK_20260612_8888.JPG) into (date_str, cam_num).
    Returns None if the filename does not match the dated format.
    """
    pattern = rf"^{re.escape(prefix)}(\d{{8}})_(\d{{{CAMERA_SEQ_WIDTH}}})\."
    m = re.match(pattern, filename, re.IGNORECASE)
    if m:
        date_str, cam_num = m.group(1), int(m.group(2))
        logging.debug("Extracted dated parts (%s, %d) from %s", date_str, cam_num, filename)
        return date_str, cam_num
    logging.debug("No dated parts found in %s", filename)
    return None


def generate_dated_filename(cam_num: int, date_str: str, ext: str, prefix: str = "PICT") -> str:
    """
    Generate a dated filename from camera sequence number and shoot date.

    Example: cam_num=8888, date_str='20260612', ext='.JPG', prefix='NIK_'
             -> 'NIK_20260612_8888.JPG'
    """
    name = f"{prefix}{date_str}_{cam_num:0{CAMERA_SEQ_WIDTH}d}{ext}"
    logging.debug("Generated dated filename: %s", name)
    return name


def resolve_name_conflict(base_name: str, used_names: Set[str]) -> str:
    """
    Return base_name if it is not in used_names. Otherwise append _B, _C, ...
    until a free variant is found. Only triggered when the camera counter rolled
    over within the same calendar day (extremely rare).
    """
    if base_name not in used_names:
        return base_name
    if "." in base_name:
        stem, ext = base_name.rsplit(".", 1)
        ext = f".{ext}"
    else:
        stem, ext = base_name, ""
    # Start from B because the unmodified base_name is implicitly the A slot.
    for suffix in "BCDEFGHIJKLMNOPQRSTUVWXYZ":
        candidate = f"{stem}_{suffix}{ext}"
        if candidate not in used_names:
            logging.warning("Name conflict resolved: %s -> %s", base_name, candidate)
            return candidate
    raise ValueError(f"No available name variant for {base_name}")


def extract_numeric_suffix(filename: str, prefix: str = "PICT", width: int = 6) -> Optional[int]:
    """
    Extract a 4-6 digit numeric suffix from a legacy filename for backward-compatible
    hash-map lookup against old-format files still present in the reference folder.
    """
    pattern = rf"^{re.escape(prefix)}(\d{{{MIN_NUMBER_WIDTH},{MAX_NUMBER_WIDTH}}})\."
    m = re.match(pattern, filename, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None
