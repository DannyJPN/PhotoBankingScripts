"""
Unit tests for detect_camera_from_filename with the dated names produced by pullnewmediatounsorted.

The dated format is ``<prefix>YYYYMMDD_XXXX`` with an optional conflict suffix ``_B`` .. ``_Z``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "sortunsortedmedia"
sys.path.insert(0, str(package_root))

import sortunsortedmedialib.media_classifier as media_classifier


@pytest.mark.parametrize(
    ("name", "camera"),
    [
        ("NIK_1797", "Nikon Z50"),
        ("NIK_20260612_1797", "Nikon Z50"),
        ("NIK_20260612_1797_B", "Nikon Z50"),
        ("NIK_20260612_1797_Z", "Nikon Z50"),
        ("PICT0195", "Bunaty Micro 4K"),
        ("PICT000195", "Bunaty Micro 4K"),
        ("PICT20260612_0195", "Bunaty Micro 4K"),
        ("PICT20260612_0195_B", "Bunaty Micro 4K"),
    ],
)
def test_media_classifier__detect_camera_from_filename__legacy_and_dated_names(name: str, camera: str) -> None:
    """Legacy and dated names of the same camera give the same camera."""
    assert media_classifier.detect_camera_from_filename(name) == camera


@pytest.mark.parametrize(
    "name",
    [
        "NIK_20260612_179",
        "NIK_20260612_17977",
        "NIK_2026061_1797",
        "NIK_20260612_1797_BB",
        "NIK_20260612_1797_1",
        "PICT20260612_0195_b",
        "PICT20260612-0195",
    ],
)
def test_media_classifier__detect_camera_from_filename__malformed_dated_names_unknown(name: str) -> None:
    """Names that only resemble the dated format are not attributed to a camera."""
    assert media_classifier.detect_camera_from_filename(name) == "Unknown"


def test_media_classifier__detect_camera_from_filename__dated_name_not_samsung() -> None:
    """A bare ``YYYYMMDD_HHMMSS`` name stays a Samsung name and a dated Nikon name does not become one."""
    assert media_classifier.detect_camera_from_filename("20210729_141633") == "Samsung J320FN"
    assert media_classifier.detect_camera_from_filename("NIK_20210729_1416") == "Nikon Z50"
