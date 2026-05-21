"""Perceptual image hashing utilities (pHash, dHash)."""

import io
import logging
from typing import Union

import imagehash
from PIL import Image


def generate_phash(image_data: Union[bytes, str]) -> imagehash.ImageHash:
    """Compute perceptual hash (pHash) for an image.

    :param image_data: Either raw image bytes or a file path string.
    :return: imagehash.ImageHash object.
    :raises Exception: If the image cannot be loaded or hashed.
    """
    return imagehash.phash(_load_image(image_data))


def generate_dhash(image_data: Union[bytes, str]) -> imagehash.ImageHash:
    """Compute difference hash (dHash) for an image.

    :param image_data: Either raw image bytes or a file path string.
    :return: imagehash.ImageHash object.
    :raises Exception: If the image cannot be loaded or hashed.
    """
    return imagehash.dhash(_load_image(image_data))


def hamming_distance(hash1: imagehash.ImageHash, hash2: imagehash.ImageHash) -> int:
    """Return the Hamming distance between two perceptual hashes.

    :param hash1: First hash.
    :param hash2: Second hash.
    :return: Number of differing bits (0 = identical).
    """
    return hash1 - hash2


def _load_image(image_data: Union[bytes, str]) -> Image.Image:
    """Load a PIL Image from bytes or file path.

    :param image_data: Raw bytes or file path.
    :return: PIL Image converted to RGB.
    """
    if isinstance(image_data, (bytes, bytearray)):
        return Image.open(io.BytesIO(image_data)).convert("RGB")
    return Image.open(image_data).convert("RGB")
