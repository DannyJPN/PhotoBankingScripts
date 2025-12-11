import os
import hashlib
import logging
from typing import Dict
from tqdm import tqdm

try:
    import xxhash
    XXHASH_AVAILABLE = True
except ImportError:
    XXHASH_AVAILABLE = False
    logging.warning("xxhash not available, falling back to MD5. Install with: pip install xxhash")


def compute_file_hash(path: str, method: str = "xxhash64") -> str:
    """
    Compute file hash using specified algorithm.

    Args:
        path: Path to file to hash
        method: Hash algorithm ("xxhash64", "md5", "sha256")

    Returns:
        Hex digest of file hash

    Note:
        xxhash64 is 10-15x faster than MD5 for large files.
        Falls back to MD5 if xxhash is not installed.
    """
    logging.debug("Computing %s hash for file: %s", method, path)
    try:
        if method == "xxhash64":
            if not XXHASH_AVAILABLE:
                logging.warning("xxhash not available, using MD5 fallback for %s", path)
                method = "md5"
            else:
                h = xxhash.xxh64()
                with open(path, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):  # 64KB chunks for better performance
                        h.update(chunk)
                result = h.hexdigest()
                logging.debug("Computed xxhash64 hash for %s: %s", path, result)
                return result

        # Fallback to hashlib for other methods (md5, sha256, etc.)
        h = hashlib.new(method)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        result = h.hexdigest()
        logging.debug("Computed %s hash for %s: %s", method, path, result)
        return result
    except Exception as e:
        logging.error("Failed to compute hash for %s: %s", path, e)
        raise


