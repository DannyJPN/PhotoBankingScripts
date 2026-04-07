import os
import argparse
import logging
import re

from shared.utils            import get_log_filename
from shared.file_operations import ensure_directory, unify_duplicate_files, copy_folder, flatten_folder, move_folder_contents
from shared.logging_config  import setup_logging

from pullnewmediatounsortedlib.constants import (
    DEFAULT_RAID_DRIVE,
    DEFAULT_DROPBOX,
    DEFAULT_GDRIVE,
    DEFAULT_ONEDRIVE_AUTO,
    DEFAULT_ONEDRIVE_MANUAL,
    DEFAULT_SNAPBRIDGE,
    DEFAULT_SCREEN_ONEDRIVE,
    DEFAULT_SCREEN_DROPBOX,
    DEFAULT_ACCOUNT_FOLDER,
    DEFAULT_TARGET_FOLDER,
    DEFAULT_TARGET_SCREEN_FOLDER,
    DEFAULT_FINAL_TARGET_FOLDER,
    DEFAULT_LOG_DIR,
    SCREENSHOT_MARKERS,
    PREFIXES_TO_NORMALIZE,
)

from pullnewmediatounsortedlib.renaming         import replace_in_filenames
from pullnewmediatounsortedlib.renaming import normalize_indexed_filenames


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Pull new photos to unsorted folder."
    )
    parser.add_argument("--raid_drive",      type=str, default=DEFAULT_RAID_DRIVE)
    parser.add_argument("--dropbox",         type=str, default=DEFAULT_DROPBOX)
    parser.add_argument("--gdrive",          type=str, default=DEFAULT_GDRIVE)
    parser.add_argument("--onedrive_auto",   type=str, default=DEFAULT_ONEDRIVE_AUTO)
    parser.add_argument("--onedrive_manual", type=str, default=DEFAULT_ONEDRIVE_MANUAL)
    parser.add_argument("--snapbridge",      type=str, default=DEFAULT_SNAPBRIDGE)
    parser.add_argument("--screens_onedrive",type=str, default=DEFAULT_SCREEN_ONEDRIVE)
    parser.add_argument("--screens_dropbox", type=str, default=DEFAULT_SCREEN_DROPBOX)
    parser.add_argument("--account_folder",  type=str, default=DEFAULT_ACCOUNT_FOLDER)
    parser.add_argument("--target",          type=str, default=DEFAULT_TARGET_FOLDER)
    parser.add_argument("--target_screen",   type=str, default=DEFAULT_TARGET_SCREEN_FOLDER)
    parser.add_argument("--final_target",    type=str, default=DEFAULT_FINAL_TARGET_FOLDER)
    parser.add_argument("--log_dir",         type=str, default=DEFAULT_LOG_DIR)
    parser.add_argument("--debug",           action="store_true")
    parser.add_argument("--index_prefix",    type=str, default="PICT", help="Prefix for indexed filenames")
    parser.add_argument("--index_width",     type=int, default=4, help="Width of numeric suffix")
    parser.add_argument("--index_max",       type=int, default=9999, help="Max index number to scan")
    parser.add_argument("--move",            action="store_true", help="Move files instead of copy")
    return parser.parse_args()


def main():
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)
    logging.info("Starting sync process")

    # Define source and screenshot folders
    sources = [
        args.raid_drive,
        args.dropbox,
        args.gdrive,
        args.onedrive_auto,
        args.onedrive_manual,
        args.snapbridge,
        args.account_folder,
    ]
    screen_sources = [args.screens_onedrive, args.screens_dropbox]

    # 0) Unify duplicates before any renaming
    for folder in sources + screen_sources + [args.target]:
        unify_duplicate_files(folder, recursive=True)

    # 1) Generic filename replacements (_NIK -> NIK_ by default)
    for folder in sources + screen_sources + [args.target]:
        replace_in_filenames(folder, "_NIK", "NIK_", recursive=True)

    # 2) Normalize indexed filenames in target vs final_target
    for prefix in PREFIXES_TO_NORMALIZE:
        normalize_indexed_filenames(
            source_folder=args.target,
            reference_folder=args.final_target,
            prefix=prefix,
            width=args.index_width,
            max_number=args.index_max,
        )

    # 3) Normalize indexed filenames in sources vs target
    for folder in sources + screen_sources:
        for prefix in PREFIXES_TO_NORMALIZE:
            normalize_indexed_filenames(
                source_folder=folder,
                reference_folder=args.target,
                prefix=prefix,
                width=args.index_width,
                max_number=args.index_max,
            )

    # 4) Copy or move media files to target
    for folder in sources:
        if args.move:
            move_folder_contents(folder, args.target)
        else:
            copy_folder(folder, args.target)

    # 5) Copy or move screenshot files to target_screen
    pattern = rf"(?:{'|'.join(re.escape(m) for m in SCREENSHOT_MARKERS)})"
    for folder in sources + screen_sources:
        if args.move:
            move_folder_contents(folder, args.target_screen, pattern=pattern)
        else:
            copy_folder(folder, args.target_screen, pattern=pattern)

    # 6) Flatten target folder structure (move all files to root level)
    logging.info("Flattening target folder structure")
    flatten_folder(args.target)
    flatten_folder(args.target_screen)

    # 7) Ensure temporary directory exists
    temp_dir = os.path.join(args.target, "FotoTemp")
    ensure_directory(temp_dir)

    logging.info("Sync process completed successfully")


if __name__ == "__main__":
    main()
