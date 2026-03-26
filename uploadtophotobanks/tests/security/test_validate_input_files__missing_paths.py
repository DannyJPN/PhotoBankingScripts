"""
Security-focused tests for input validation.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

import uploadtophotobanks


def test_validate_input_files_missing_media(monkeypatch):
    args = types.SimpleNamespace(
        media_folder="X:/missing_media",
        export_dir="X:/export",
    )

    monkeypatch.setattr(uploadtophotobanks.os.path, "exists", lambda _p: False)
    assert uploadtophotobanks.validate_input_files(args) is False
