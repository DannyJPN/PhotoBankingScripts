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

from tqdm import tqdm

sys.path.insert(0, os.path.dirname(__file__))

from shared.exif_handler import get_best_creation_date
from shared.exif_downloader import ensure_exiftool
from shared.logging_config import setup_logging
from shared.utils import get_log_filename
from shared.file_operations import compute_file_hash, ensure_directory, list_files, move_file
from shared.name_utils import (
    extract_camera_number,
    generate_dated_filename,
    name_key,
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
    parser.add_argument(
        "--folder", type=str, default=DEFAULT_FINAL_TARGET_FOLDER, help="Folder to migrate (default: J:/)"
    )
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Preview renames without executing them")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def collect_legacy_files(folder: str, prefixes: list[str]) -> list[Path]:
    """Return all files that match a legacy prefix + 4-digit suffix pattern."""
    result = []
    for path in list_files(folder, recursive=True):
        f = Path(path)
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

    # Case-insensitive name key -> owning file, seeded with ALL existing files (legacy and already dated)
    used_names: dict[str, Path] = {}
    for path in list_files(folder, recursive=True):
        f = Path(path)
        used_names[name_key(f.name)] = f

    known_hash: dict[Path, str] = {}

    def _hash_of(path: Path) -> str:
        if path not in known_hash:
            known_hash[path] = compute_file_hash(str(path))
        return known_hash[path]

    renamed = 0
    skipped = 0
    conflicts = 0

    path_to_date: dict[Path, datetime] = {}
    for file_path in tqdm(files, desc="Reading EXIF dates", unit="file"):
        path_to_date[file_path] = _date(str(file_path))

    for file_path in tqdm(sorted(files, key=lambda p: path_to_date[p]), desc="Migrating filenames", unit="file"):
        name = file_path.name
        ext = file_path.suffix

        # Determine prefix
        prefix = next((p for p in PREFIXES_TO_NORMALIZE if extract_camera_number(name, prefix=p) is not None), None)
        if prefix is None:
            logging.warning("Could not determine prefix for %s, skipping", name)
            skipped += 1
            continue

        cam_num = extract_camera_number(name, prefix=prefix)
        date_str = path_to_date[file_path].strftime(DATE_FORMAT)
        try:
            base_new_name = generate_dated_filename(cam_num, date_str, ext, prefix=prefix)
        except ValueError as e:
            logging.warning("Cannot build dated name for %s: %s, skipping", name, e)
            skipped += 1
            continue

        # Release the file's own name so it does not block itself
        own_key = name_key(name)
        owned = used_names.get(own_key) == file_path
        if owned:
            del used_names[own_key]
        try:
            new_name = resolve_name_conflict(
                base_new_name,
                used_names,
                same_content=lambda key: _hash_of(used_names[key]) == _hash_of(file_path),
            )
        except ValueError:
            logging.error("No name variant available for %s, skipping", base_new_name)
            if owned:
                used_names[own_key] = file_path
            skipped += 1
            continue
        used_names[name_key(new_name)] = file_path

        if name_key(new_name) == name_key(name):
            skipped += 1
            continue

        if new_name != base_new_name:
            conflicts += 1
            logging.warning("Conflict resolved: %s -> %s (base was %s)", name, new_name, base_new_name)

        dst = file_path.parent / new_name
        if dry_run:
            logging.info("[DRY-RUN] %s -> %s", name, new_name)
            renamed += 1
        else:
            try:
                move_file(str(file_path), str(dst), overwrite=False)
                if file_path.exists():
                    logging.warning("Rename skipped, destination already exists: %s -> %s", name, new_name)
                    used_names.pop(name_key(new_name), None)
                    if owned:
                        used_names[own_key] = file_path
                    skipped += 1
                else:
                    logging.info("Renamed %s -> %s", name, new_name)
                    used_names[name_key(new_name)] = dst
                    renamed += 1
            except Exception as e:
                logging.error("Failed to rename %s: %s", name, e)
                used_names.pop(name_key(new_name), None)
                if owned:
                    used_names[own_key] = file_path
                skipped += 1

    logging.info(
        "Migration complete. Renamed: %d  Skipped: %d  Conflicts resolved: %d",
        renamed,
        skipped,
        conflicts,
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
