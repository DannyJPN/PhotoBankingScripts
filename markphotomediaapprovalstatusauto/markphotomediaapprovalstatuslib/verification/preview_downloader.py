"""Downloads and locally caches preview images from photobank CDN URLs."""

import hashlib
import logging
import os
from typing import Optional

from markphotomediaapprovalstatuslib.transport.http_client import HttpClient


def download_preview(url: str, http_client: HttpClient, cache_dir: str) -> Optional[bytes]:
    """Download a preview image, returning cached bytes when available.

    :param url: Direct URL to the preview / thumbnail image.
    :param http_client: Shared HttpClient instance.
    :param cache_dir: Directory for caching downloaded previews.
    :return: Raw image bytes, or None if the download fails.
    """
    cache_key = hashlib.md5(url.encode()).hexdigest()
    cache_path = os.path.join(cache_dir, cache_key)

    if os.path.exists(cache_path):
        logging.debug("Preview cache hit: %s", url)
        with open(cache_path, "rb") as fh:
            return fh.read()

    try:
        response = http_client.get(url)
        data = response.content
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_path, "wb") as fh:
            fh.write(data)
        logging.debug("Downloaded and cached preview: %s", url)
        return data
    except Exception as exc:
        logging.warning("Failed to download preview from %s: %s", url, exc)
        return None
