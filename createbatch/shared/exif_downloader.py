import logging
import os
import platform
import zipfile
import tarfile
from urllib.request import urlretrieve
from shared.file_operations import ensure_directory

a = os

EXIFTOOL_URLS = {
    'Windows_64bit': 'https://exiftool.org/exiftool-13.27_64.zip',
    'Windows_32bit': 'https://exiftool.org/exiftool-13.27_32.zip',
    'Linux': 'https://exiftool.org/Image-ExifTool-13.27.tar.gz',
    'Darwin': 'https://exiftool.org/Image-ExifTool-13.27.tar.gz'
}

def ensure_exiftool(tool_dir: str) -> str:
    """
    Ensure that ExifTool is available in the given directory.
    Downloads and extracts the tool if not present.
    Supports Windows ZIP (with exiftool(-k).exe), Linux/macOS tarball.

    Returns:
        Full path to the ExifTool executable.
    """
    logging.debug("Ensuring ExifTool in %s", tool_dir)
    ensure_directory(tool_dir)

    system = platform.system()
    arch, _ = platform.architecture()

    if system == 'Windows':
        key = 'Windows_64bit' if '64' in arch else 'Windows_32bit'
    elif system in ('Linux', 'Darwin'):
        key = system
    else:
        raise RuntimeError(f"Unsupported platform for ExifTool: {system}")

    url = EXIFTOOL_URLS.get(key)
    if not url:
        raise RuntimeError(f"No ExifTool download URL for platform/arch {key}")

    # Prepare paths
    exe_name = 'exiftool.exe' if system == 'Windows' else 'exiftool'
    exe_path = os.path.join(tool_dir, exe_name)
    # If already have executable and it works, return
    if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
        logging.info("ExifTool already present at %s", exe_path)
        return exe_path

    # Download archive
    logging.info("Downloading ExifTool from %s", url)
    archive_name = os.path.basename(url)
    archive_path = os.path.join(tool_dir, archive_name)
    urlretrieve(url, archive_path)
    logging.debug("Downloaded archive to %s", archive_path)

    # Extract contents
    if archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zf:
            zf.extractall(tool_dir)
    else:
        with tarfile.open(archive_path, 'r:gz') as tf:
            tf.extractall(tool_dir)
    os.remove(archive_path)
    logging.info("Extracted ExifTool archive in %s", tool_dir)

    # Locate executable in extracted structure
    exe = None
    for root, _, files in os.walk(tool_dir):
        for fname in files:
            lower = fname.lower()
            if system == 'Windows' and lower.startswith('exiftool') and lower.endswith('.exe'):
                exe = os.path.join(root, fname)
                break
            if system != 'Windows' and fname == 'exiftool':
                exe = os.path.join(root, fname)
                break
        if exe:
            break

    if not exe:
        raise RuntimeError(f"ExifTool executable not found after extraction in {tool_dir}")

    # Ensure executable permissions
    try:
        os.chmod(exe, 0o755)
    except Exception:
        pass

    logging.info("Located ExifTool executable at %s", exe)
    return exe