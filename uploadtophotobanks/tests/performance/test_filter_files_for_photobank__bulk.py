"""
Performance-oriented tests for file filtering per photobank.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

from uploadtophotobanksslib.uploader import PhotobankUploader


def test_filter_files_for_photobank_bulk():
    uploader = PhotobankUploader(credentials={})
    media_files = [f"C:/media/file_{i}.jpg" for i in range(300)]
    media_files += [f"C:/media/file_{i}.mp4" for i in range(200)]
    filtered = uploader._filter_files_for_photobank(media_files, "ShutterStock")
    assert len(filtered) >= 300
