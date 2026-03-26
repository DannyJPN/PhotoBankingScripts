"""Unit tests for image_hasher.py."""

import io

from PIL import Image

from markphotomediaapprovalstatuslib.verification.image_hasher import (
    generate_dhash,
    generate_phash,
    hamming_distance,
)


def _make_image_bytes(color: tuple = (128, 64, 32), size: tuple = (64, 64)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_generate_phash__returns_hash_from_bytes():
    h = generate_phash(_make_image_bytes())
    assert h is not None


def test_generate_dhash__returns_hash_from_bytes():
    h = generate_dhash(_make_image_bytes())
    assert h is not None


def test_hamming_distance__identical_images_returns_zero():
    data = _make_image_bytes()
    assert hamming_distance(generate_phash(data), generate_phash(data)) == 0


def test_hamming_distance__different_images_returns_nonzero():
    h1 = generate_phash(_make_image_bytes(color=(0, 0, 0)))
    h2 = generate_phash(_make_image_bytes(color=(255, 255, 255)))
    assert hamming_distance(h1, h2) > 0


def test_generate_phash__jpeg_compression_low_distance():
    original = _make_image_bytes(color=(100, 150, 200), size=(128, 128))
    img = Image.open(io.BytesIO(original))
    compressed = io.BytesIO()
    img.save(compressed, format="JPEG", quality=30)
    h1 = generate_phash(original)
    h2 = generate_phash(compressed.getvalue())
    assert hamming_distance(h1, h2) <= 10