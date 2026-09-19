"""
Unit tests for removealreadysortedout/shared/name_utils.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "removealreadysortedout"
sys.path.insert(0, str(package_root))

import shared.name_utils as name_utils


def test_extract_camera_number__matches_four_digit_prefix():
    assert name_utils.extract_camera_number("NIK_0001.JPG", prefix="NIK_") == 1


def test_extract_camera_number__matches_five_and_six_digit_legacy():
    assert name_utils.extract_camera_number("NIK_012345.JPG", prefix="NIK_") == 12345
    assert name_utils.extract_camera_number("NIK_123456.JPG", prefix="NIK_") == 123456


def test_extract_camera_number__no_match_returns_none():
    assert name_utils.extract_camera_number("NOPE.jpg", prefix="NIK_") is None
    assert name_utils.extract_camera_number("NIK_20260612_0001.JPG", prefix="NIK_") is None


def test_extract_dated_parts__valid_dated_filename():
    assert name_utils.extract_dated_parts("NIK_20260612_8888.JPG", prefix="NIK_") == ("20260612", 8888)


def test_extract_dated_parts__legacy_filename_returns_none():
    assert name_utils.extract_dated_parts("NIK_0001.JPG", prefix="NIK_") is None


def test_generate_dated_filename__formats_with_padding():
    assert name_utils.generate_dated_filename(12, "20260612", ".JPG", prefix="NIK_") == "NIK_20260612_0012.JPG"


def test_resolve_name_conflict__no_conflict_returns_base_name():
    assert name_utils.resolve_name_conflict("NIK_20260612_0001.JPG", set()) == "NIK_20260612_0001.JPG"


def test_resolve_name_conflict__single_conflict_appends_suffix():
    used = {"NIK_20260612_0001.JPG"}
    assert name_utils.resolve_name_conflict("NIK_20260612_0001.JPG", used) == "NIK_20260612_0001_B.JPG"


def test_resolve_name_conflict__exhaustion_raises_value_error():
    base = "NIK_20260612_0001.JPG"
    stem, ext = base.rsplit(".", 1)
    used = {base} | {f"{stem}_{suffix}.{ext}" for suffix in "BCDEFGHIJKLMNOPQRSTUVWXYZ"}
    try:
        name_utils.resolve_name_conflict(base, used)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_extract_numeric_suffix__matches_prefix():
    assert name_utils.extract_numeric_suffix("PICT0012.jpg") == 12
    assert name_utils.extract_numeric_suffix("NOPE.jpg") is None


def test_generate_dated_filename__max_camera_number_round_trips():
    name = name_utils.generate_dated_filename(9999, "20260612", ".JPG", prefix="NIK_")
    assert name == "NIK_20260612_9999.JPG"
    assert name_utils.extract_dated_parts(name, prefix="NIK_") == ("20260612", 9999)


def test_generate_dated_filename__number_above_four_digits_raises():
    for too_wide in (10000, 12345, 123456):
        try:
            name_utils.generate_dated_filename(too_wide, "20260612", ".JPG", prefix="NIK_")
            assert False, "expected ValueError"
        except ValueError as exc:
            assert "does not fit" in str(exc)


def test_generate_dated_filename__negative_number_raises():
    try:
        name_utils.generate_dated_filename(-1, "20260612", ".JPG", prefix="NIK_")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_wide_legacy_number_is_parsed_but_cannot_be_dated():
    assert name_utils.extract_camera_number("NIK_012345.JPG", prefix="NIK_") == 12345
    try:
        name_utils.generate_dated_filename(12345, "20260612", ".JPG", prefix="NIK_")
        assert False, "expected ValueError"
    except ValueError:
        pass
