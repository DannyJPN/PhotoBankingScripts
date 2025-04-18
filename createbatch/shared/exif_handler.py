import logging
import subprocess
import os
import shutil
from typing import Dict

def update_exif_metadata(file_path: str, metadata: Dict[str, str], tool_path: str = None) -> None:
    """
    Update metadata for a given media file using the ExifTool command-line tool across platforms.
    Ensures that creation date, title, description, and keywords are set correctly.

    Args:
        file_path: Path to the media file to update.
        metadata: Dict with keys:
            - 'datetimeoriginal': original creation date/time (string)
            - 'title': title/caption
            - 'description': description text
            - 'keywords': comma-separated keywords
        tool_path: Optional path to ExifTool executable or directory containing it.
                   If None or not found, will attempt to locate ExifTool in system PATH.
    """
    logging.debug("Preparing to update EXIF metadata for %s with %s", file_path, metadata)

    # Determine ExifTool executable
    exe = None
    # If provided a directory, look inside
    if tool_path and os.path.isdir(tool_path):
        base = 'exiftool.exe' if os.name == 'nt' else 'exiftool'
        candidate = os.path.join(tool_path, base)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            exe = candidate
    # If provided a file path directly
    if not exe and tool_path and os.path.isfile(tool_path) and os.access(tool_path, os.X_OK):
        exe = tool_path
    # Fallback to system PATH
    if not exe:
        exe = shutil.which('exiftool')
    if not exe:
        raise RuntimeError('ExifTool executable not found. Please install ExifTool or provide its path.')

    logging.debug("Using ExifTool executable at %s", exe)

    # Base arguments: overwrite original, set file creation from original timestamp, and keyword separator
    args = [exe, '-overwrite_original', '-FileCreateDate<DateTimeOriginal', '-sep', ',']

    # Map metadata keys to ExifTool tags
    tag_map = {
        'datetimeoriginal': '-DateTimeOriginal',
        'title': '-Title',
        'description': '-Description',
        'keywords': '-Keywords'
    }
    # Append each tag assignment if provided
    for key, tag in tag_map.items():
        value = metadata.get(key)
        if value:
            args.append(f"{tag}={value}")

    # Add target file
    args.append(file_path)

    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        logging.debug("ExifTool stdout: %s", result.stdout.strip())
        logging.debug("EXIF metadata updated successfully for %s", file_path)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else ''
        logging.error(
            "ExifTool failed for %s with return code %d and error: %s",
            file_path, e.returncode, stderr
        )
        raise
