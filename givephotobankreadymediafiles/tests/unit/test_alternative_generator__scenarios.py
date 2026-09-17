"""
Unit tests for givephotobankreadymediafileslib/alternative_generator.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import alternative_generator


class DummyImage:
    def __init__(self, mode="RGB"):
        self.mode = mode
        self.saved = []

    def convert(self, _mode):
        self.mode = _mode
        return self

    def save(self, path, _fmt=None, **_kwargs):
        self.saved.append(path)

    def filter(self, _filter):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


def test_generate_all_versions__missing_file(monkeypatch):
    monkeypatch.setattr(alternative_generator.os.path, "exists", lambda _p: False)
    generator = alternative_generator.AlternativeGenerator(enabled_alternatives=[], enabled_formats=[])

    assert generator.generate_all_versions("C:/missing.jpg", "C:/out", "C:/edit") == []


def test_generate_all_versions__unsupported_extension(monkeypatch):
    monkeypatch.setattr(alternative_generator.os.path, "exists", lambda _p: True)
    generator = alternative_generator.AlternativeGenerator(enabled_alternatives=[], enabled_formats=[])

    assert generator.generate_all_versions("C:/file.txt", "C:/out", "C:/edit") == []


def test_convert_format__success(monkeypatch):
    dummy = DummyImage()
    monkeypatch.setattr(alternative_generator.Image, "open", lambda _p: dummy)
    generator = alternative_generator.AlternativeGenerator(enabled_alternatives=[], enabled_formats=[".png"])

    ok = generator._convert_format("C:/file.jpg", "C:/out/file.png", ".png")
    assert ok is True
    assert dummy.saved


def test_convert_format__unsupported_format(monkeypatch):
    dummy = DummyImage()
    monkeypatch.setattr(alternative_generator.Image, "open", lambda _p: dummy)
    generator = alternative_generator.AlternativeGenerator(enabled_alternatives=[], enabled_formats=[".webp"])

    ok = generator._convert_format("C:/file.jpg", "C:/out/file.webp", ".webp")
    assert ok is False


def test_generate_single_edit__missing_processor():
    generator = alternative_generator.AlternativeGenerator(enabled_alternatives=[], enabled_formats=[])
    result = generator._generate_single_edit("C:/file.jpg", "C:/out", "_unknown")
    assert result is None


def test_generate_edit_alternatives__unknown_tag_progress():
    generator = alternative_generator.AlternativeGenerator(enabled_alternatives=["_unknown"], enabled_formats=[])

    class DummyProgress:
        def __init__(self):
            self.count = 0

        def update(self, value):
            self.count += value

    progress = DummyProgress()
    result = generator._generate_edit_alternatives("C:/file.jpg", "C:/out", progress_bar=progress)

    assert result == []
    assert progress.count == 1


def test_get_alternative_output_dirs__replaces_foto():
    target_dir, edited_dir = alternative_generator.get_alternative_output_dirs(
        "I:/Rozt/Foto/jpg/Abstrakty/DSC0001.JPG"
    )

    assert target_dir.endswith("Foto/jpg/Abstrakty")
    assert "Upraven" in edited_dir


def test_get_format_conversion_path__updates_extension():
    path = alternative_generator.get_format_conversion_path(
        "I:/Rozt/Foto/jpg/Abstrakty/DSC0001.JPG", ".png"
    )
    assert path.endswith("Foto/png/Abstrakty/DSC0001.png")
