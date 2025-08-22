import hashlib
import logging


def compute_file_hash(path: str, method: str = "md5") -> str:
    logging.debug("Computing %s hash for file: %s", method, path)
    try:
        h = hashlib.new(method)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        result = h.hexdigest()
        logging.debug("Computed hash for %s: %s", path, result)
        return result
    except Exception as e:
        logging.error("Failed to compute hash for %s: %s", path, e)
        raise
