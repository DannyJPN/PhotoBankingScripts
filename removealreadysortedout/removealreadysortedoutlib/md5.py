import hashlib
import logging

def calculate_md5(file_path):
    """
    Calculate the MD5 hash of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The MD5 hash of the file.
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
    except Exception as e:
        logging.error(f"Error calculating MD5 for {file_path}: {e}", exc_info=True)
        return ""  # Return an empty string or some default value to avoid unhandled cases.
    return hash_md5.hexdigest()