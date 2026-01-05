"""
Unit tests for replace_in_filenames.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "pullnewmediatounsorted"
sys.path.insert(0, str(package_root))

from pullnewmediatounsortedlib.renaming import replace_in_filenames


def test_replace_in_filenames__renames(tmp_path):
    target = tmp_path / "photo_NIK.jpg"
    target.write_text("x", encoding="utf-8")

    replace_in_filenames(str(tmp_path), "_NIK", "NIK_", recursive=False)

    assert not target.exists()
    assert (tmp_path / "photoNIK_.jpg").exists()
