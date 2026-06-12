"""
One-time migration script: rename all legacy NIK_XXXX.JPG / PICT_XXXX.JPG files
in the final target folder (J:/) to the dated format NIK_YYYYMMDD_XXXX.JPG.

The shoot date is determined by get_best_creation_date (minimum over all EXIF date
tags), which is the same algorithm used by normalize_indexed_filenames.

Usage:
    python migrate_to_dated_filenames.py [--folder J:/] [--dry-run] [--debug]

Pass --dry-run to preview all planned renames without executing them.
"""
import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from shared.exif_handler import get_best_creation_date
from shared.exif_downloader import ensure_exiftool
from shared.logging_config import setup_logging
from shared.utils import get_log_filename
from shared.file_operations import ensure_directory
from shared.name_utils import (
    extract_camera_number,
    extract_dated_parts,
    generate_dated_filename,
    resolve_name_conflict,
)
from pullnewmediatounsortedlib.constants import (
    DEFAULT_FINAL_TARGET_FOLDER,
    DEFAULT_LOG_DIR,
    DATE_FORMAT,
    PREFIXES_TO_NORMALIZE,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate legacy NIK_/PICT_ filenames to dated format.")
    parser.add_argument("--folder",  type=str, default=DEFAULT_FINAL_TARGET_FOLDER,
                        help="Folder to migrate (default: J:/)")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR)
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview renames without executing them")
    parser.add_argument("--debug",   action="store_true")
    return parser.parse_args()


def collect_legacy_files(folder: str, prefixes: list[str]) -> list[Path]:
    """Return all files that match a legacy prefix + 4-digit suffix pattern."""
    result = []
    for f in Path(folder).rglob("*"):
        if not f.is_file():
            continue
        for prefix in prefixes:
            if extract_camera_number(f.name, prefix=prefix) is not None:
                result.append(f)
                break
    return result


def migrate(folder: str, dry_run: bool) -> None:
    if not os.path.exists(folder):
        logging.error("Folder not found: %s", folder)
        sys.exit(1)

    try:
        exiftool_path = ensure_exiftool()
    except FileNotFoundError as e:
        logging.warning("ExifTool not found, will use filesystem dates: %s", e)
        exiftool_path = None

    def _date(path: str) -> datetime:
        d = get_best_creation_date(path, tool_path=exiftool_path)
        if d is None:
            try:
                d = datetime.fromtimestamp(os.path.getmtime(path))
            except Exception:
                d = datetime.fromtimestamp(0)
        return d

    files = collect_legacy_files(folder, PREFIXES_TO_NORMALIZE)
    logging.info("Found %d legacy files to migrate in %s", len(files), folder)

    used_names: set[str] = set()

    # Seed used_names with ALL existing filenames in the folder (both legacy and already-dated)
    for f in Path(folder).rglob("*"):
        if f.is_file():
            used_names.add(f.name)

    renamed = 0
    skipped = 0
    conflicts = 0

    for file_path in sorted(files, key=lambda p: _date(str(p))):
        name = file_path.name
        ext = file_path.suffix

        # Determine prefix
        prefix = next((p for p in PREFIXES_TO_NORMALIZE if extract_camera_number(name, prefix=p) is not None), None)
        if prefix is None:
            logging.warning("Could not determine prefix for %s, skipping", name)
            skipped += 1
            continue

        cam_num = extract_camera_number(name, prefix=prefix)
        date_str = _date(str(file_path)).strftime(DATE_FORMAT)
        base_new_name = generate_dated_filename(cam_num, date_str, ext, prefix=prefix)

        # Remove old name from used_names so it doesn't block itself
        used_names.discard(name)
        new_name = resolve_name_conflict(base_new_name, used_names)
        used_names.add(new_name)

        if new_name == name:
            skipped += 1
            continue

        if new_name != base_new_name:
            conflicts += 1
            logging.warning("Conflict resolved: %s -> %s (base was %s)", name, new_name, base_new_name)

        dst = file_path.parent / new_name
        if dry_run:
            logging.info("[DRY-RUN] %s -> %s", name, new_name)
        else:
            try:
                os.rename(str(file_path), str(dst))
                logging.info("Renamed %s -> %s", name, new_name)
                renamed += 1
            except Exception as e:
                logging.error("Failed to rename %s: %s", name, e)
                skipped += 1

    logging.info(
        "Migration complete. Renamed: %d  Skipped: %d  Conflicts resolved: %d",
        renamed, skipped, conflicts,
    )


def main() -> None:
    args = parse_arguments()
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    if args.dry_run:
        logging.info("DRY-RUN mode: no files will be changed")

    migrate(args.folder, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
