import re
import logging
from collections.abc import Callable, Container

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pullnewmediatounsortedlib.constants import (
    CAMERA_SEQ_WIDTH,
    MIN_NUMBER_WIDTH,
    MAX_NUMBER_WIDTH,
)


def extract_camera_number(filename: str, prefix: str = "PICT") -> int | None:
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


def extract_dated_parts(filename: str, prefix: str = "PICT") -> tuple[str, int] | None:
    """
    Parse a dated filename (e.g. NIK_20260612_8888.JPG) into (date_str, cam_num).
    A conflict suffix (_B, _C, ...) is accepted so that suffixed files stay recognised as dated.
    Returns None if the filename does not match the dated format.
    """
    pattern = rf"^{re.escape(prefix)}(\d{{8}})_(\d{{{CAMERA_SEQ_WIDTH}}})(?:_[A-Z])?\."
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

    :param cam_num: Camera sequence number, must fit into CAMERA_SEQ_WIDTH digits.
    :param date_str: Shoot date formatted with DATE_FORMAT.
    :param ext: File extension including the leading dot.
    :param prefix: Filename prefix (e.g. ``NIK_``).
    :return: The dated filename.
    :raises ValueError: If cam_num does not fit into CAMERA_SEQ_WIDTH digits. A wider number
        would produce a name that extract_dated_parts cannot parse back, so the file would
        never be recognised as already dated.
    """
    max_num = 10**CAMERA_SEQ_WIDTH - 1
    if not 0 <= cam_num <= max_num:
        raise ValueError(f"Camera number {cam_num} does not fit into {CAMERA_SEQ_WIDTH} digits (max {max_num})")
    name = f"{prefix}{date_str}_{cam_num:0{CAMERA_SEQ_WIDTH}d}{ext}"
    logging.debug("Generated dated filename: %s", name)
    return name


def name_key(name: str) -> str:
    """
    Return the key used to compare filenames.

    Comparison is case-insensitive because the target platform (Windows/NTFS) treats
    ``a.JPG`` and ``a.jpg`` as the same file.

    :param name: Filename (basename only).
    :return: Case-folded filename.
    """
    return name.lower()


def resolve_name_conflict(
    base_name: str,
    used_names: Container[str],
    same_content: Callable[[str], bool] | None = None,
) -> str:
    """
    Return base_name if it is free. Otherwise append _B, _C, ... until a free variant is found.

    All comparisons are case-insensitive, so ``used_names`` must contain keys produced by
    :func:`name_key`.

    :param base_name: Preferred filename.
    :param used_names: Container of name keys that are already taken.
    :param same_content: Optional callable receiving the key of a taken name. It returns True
        when the current owner of that name has the same content as the file being renamed.
        Such a collision is an identical duplicate copy, not a real conflict, so base_name is
        returned unchanged.
    :return: A filename that is not taken.
    :raises ValueError: If no free variant is left. Only the suffixes B..Z (25 variants) are
        tried; the cap is deliberate because more than a handful of conflicts on one day
        indicates a real problem that needs manual attention.
    """
    key = name_key(base_name)
    if key not in used_names:
        return base_name
    if same_content is not None and same_content(key):
        logging.debug("Name %s is already used by an identical file, keeping it", base_name)
        return base_name
    if "." in base_name:
        stem, ext = base_name.rsplit(".", 1)
        ext = f".{ext}"
    else:
        stem, ext = base_name, ""
    for suffix in "BCDEFGHIJKLMNOPQRSTUVWXYZ":
        candidate = f"{stem}_{suffix}{ext}"
        if name_key(candidate) not in used_names:
            logging.warning("Name conflict resolved: %s -> %s", base_name, candidate)
            return candidate
    raise ValueError(f"No available name variant for {base_name}")
