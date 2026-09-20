"""
Unit tests for pullnewmediatounsorted/shared/name_utils.py.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "pullnewmediatounsorted"
sys.path.insert(0, str(package_root))

from shared.name_utils import (
    extract_camera_number,
    extract_dated_parts,
    generate_dated_filename,
    name_key,
    resolve_name_conflict,
)


def test_extract_camera_number__matches_four_digit_prefix():
    assert extract_camera_number("NIK_0001.JPG", prefix="NIK_") == 1


def test_extract_camera_number__matches_five_and_six_digit_legacy():
    assert extract_camera_number("NIK_012345.JPG", prefix="NIK_") == 12345
    assert extract_camera_number("NIK_123456.JPG", prefix="NIK_") == 123456


def test_extract_camera_number__case_insensitive():
    assert extract_camera_number("nik_0001.jpg", prefix="NIK_") == 1


def test_extract_camera_number__no_match_returns_none():
    assert extract_camera_number("OTHER0001.jpg", prefix="NIK_") is None
    assert extract_camera_number("NIK_20260612_0001.JPG", prefix="NIK_") is None


def test_extract_dated_parts__valid_dated_filename():
    assert extract_dated_parts("NIK_20260612_8888.JPG", prefix="NIK_") == ("20260612", 8888)


def test_extract_dated_parts__legacy_filename_returns_none():
    assert extract_dated_parts("NIK_0001.JPG", prefix="NIK_") is None


def test_extract_dated_parts__partial_match_returns_none():
    assert extract_dated_parts("NIK_2026061_8888.JPG", prefix="NIK_") is None


def test_generate_dated_filename__formats_with_padding():
    assert generate_dated_filename(12, "20260612", ".JPG", prefix="NIK_") == "NIK_20260612_0012.JPG"


def test_resolve_name_conflict__no_conflict_returns_base_name():
    assert resolve_name_conflict("NIK_20260612_0001.JPG", set()) == "NIK_20260612_0001.JPG"


def test_resolve_name_conflict__single_conflict_appends_suffix():
    used = {name_key("NIK_20260612_0001.JPG")}
    assert resolve_name_conflict("NIK_20260612_0001.JPG", used) == "NIK_20260612_0001_B.JPG"


def test_resolve_name_conflict__no_extension_filename():
    used = {name_key("NIK_20260612_0001")}
    assert resolve_name_conflict("NIK_20260612_0001", used) == "NIK_20260612_0001_B"


def test_resolve_name_conflict__exhaustion_raises_value_error():
    base = "NIK_20260612_0001.JPG"
    stem, ext = base.rsplit(".", 1)
    used = {name_key(base)} | {name_key(f"{stem}_{suffix}.{ext}") for suffix in "BCDEFGHIJKLMNOPQRSTUVWXYZ"}
    try:
        resolve_name_conflict(base, used)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_generate_dated_filename__max_camera_number_round_trips():
    name = generate_dated_filename(9999, "20260612", ".JPG", prefix="NIK_")
    assert name == "NIK_20260612_9999.JPG"
    assert extract_dated_parts(name, prefix="NIK_") == ("20260612", 9999)


def test_generate_dated_filename__number_above_four_digits_raises():
    for too_wide in (10000, 12345, 123456):
        try:
            generate_dated_filename(too_wide, "20260612", ".JPG", prefix="NIK_")
            assert False, "expected ValueError"
        except ValueError as exc:
            assert "does not fit" in str(exc)


def test_generate_dated_filename__negative_number_raises():
    try:
        generate_dated_filename(-1, "20260612", ".JPG", prefix="NIK_")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_wide_legacy_number_is_parsed_but_cannot_be_dated():
    assert extract_camera_number("NIK_012345.JPG", prefix="NIK_") == 12345
    try:
        generate_dated_filename(12345, "20260612", ".JPG", prefix="NIK_")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_extract_dated_parts__accepts_conflict_suffix():
    assert extract_dated_parts("NIK_20260612_0042_B.JPG", prefix="NIK_") == ("20260612", 42)
    assert extract_dated_parts("NIK_20260612_0042_c.jpg", prefix="NIK_") == ("20260612", 42)


def test_extract_dated_parts__rejects_longer_suffix():
    assert extract_dated_parts("NIK_20260612_0042_BB.JPG", prefix="NIK_") is None


def test_name_key__is_case_insensitive():
    assert name_key("NIK_20260612_0001.JPG") == name_key("nik_20260612_0001.jpg")


def test_resolve_name_conflict__comparison_is_case_insensitive():
    used = {name_key("NIK_20260612_0001.jpg")}
    assert resolve_name_conflict("NIK_20260612_0001.JPG", used) == "NIK_20260612_0001_B.JPG"


def test_resolve_name_conflict__suffix_candidate_checked_case_insensitively():
    used = {name_key("NIK_20260612_0001.JPG"), name_key("nik_20260612_0001_b.jpg")}
    assert resolve_name_conflict("NIK_20260612_0001.JPG", used) == "NIK_20260612_0001_C.JPG"


def test_resolve_name_conflict__identical_content_keeps_base_name():
    used = {name_key("NIK_20260612_0001.JPG")}
    assert (
        resolve_name_conflict("NIK_20260612_0001.JPG", used, same_content=lambda _key: True) == "NIK_20260612_0001.JPG"
    )


def test_resolve_name_conflict__different_content_still_gets_suffix():
    used = {name_key("NIK_20260612_0001.JPG")}
    result = resolve_name_conflict("NIK_20260612_0001.JPG", used, same_content=lambda _key: False)
    assert result == "NIK_20260612_0001_B.JPG"


def test_resolve_name_conflict__same_content_not_consulted_when_name_is_free():
    def fail(_key):
        raise AssertionError("same_content must not be called for a free name")

    assert resolve_name_conflict("NIK_20260612_0001.JPG", set(), same_content=fail) == "NIK_20260612_0001.JPG"
