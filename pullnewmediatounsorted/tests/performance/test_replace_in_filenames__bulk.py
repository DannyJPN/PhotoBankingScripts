"""
Performance-oriented tests for bulk filename replacement.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "pullnewmediatounsorted"
sys.path.insert(0, str(package_root))

from pullnewmediatounsortedlib.renaming import replace_in_filenames


def test_replace_in_filenames_bulk(tmp_path):
    folder = tmp_path / "media"
    folder.mkdir()
    for i in range(50):
        (folder / f"IMG_{i}_NIK.jpg").write_bytes(b"data")

    replace_in_filenames(str(folder), "_NIK", "NIK_", recursive=True)

    assert (folder / "IMG_1_NIK_.jpg").exists()
