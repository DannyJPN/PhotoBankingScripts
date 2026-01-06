import os
import argparse
import logging
import re
from datetime import datetime

from shared.utils            import get_log_filename
from shared.file_operations import (
    ensure_directory,
    unify_duplicate_files,
    copy_folder,
    flatten_folder,
    list_files,
    save_csv,
    save_json,
)
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
    DEFAULT_REPORT_DIR,
    DEFAULT_REPORT_FORMAT,
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
    parser.add_argument("--report-dir",      type=str, default=DEFAULT_REPORT_DIR, help="Directory for reports")
    parser.add_argument("--report-format",   type=str, default=DEFAULT_REPORT_FORMAT, choices=["csv", "json"])
    parser.add_argument("--export-report",   action="store_true", help="Export report of newly pulled files")
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

    before_media = _collect_basename_set(args.target)
    before_screens = _collect_basename_set(args.target_screen)

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

    # 4) Copy media files to target
    for folder in sources:
        copy_folder(folder, args.target)

    # 5) Copy screenshot files to target_screen
    pattern = rf"(?:{'|'.join(re.escape(m) for m in SCREENSHOT_MARKERS)})"
    for folder in sources + screen_sources:
        copy_folder(folder, args.target_screen, pattern=pattern)

    # 6) Flatten target folder structure (move all files to root level)
    logging.info("Flattening target folder structure")
    flatten_folder(args.target)
    flatten_folder(args.target_screen)

    # 7) Ensure temporary directory exists
    temp_dir = os.path.join(args.target, "FotoTemp")
    ensure_directory(temp_dir)

    if args.export_report:
        report_records = _build_new_files_report(
            before_media,
            before_screens,
            args.target,
            args.target_screen
        )
        _write_new_files_report(report_records, args.report_dir, args.report_format)

    logging.info("Sync process completed successfully")


def _collect_basename_set(folder: str) -> set[str]:
    """
    Collect lowercase basenames for files in a folder.
    """
    basenames = set()
    for path in list_files(folder, recursive=True):
        basenames.add(os.path.basename(path).lower())
    return basenames


def _build_new_files_report(
    before_media: set[str],
    before_screens: set[str],
    target_media: str,
    target_screens: str
) -> list[dict[str, str]]:
    """
    Build report records for newly pulled files.
    """
    records: list[dict[str, str]] = []
    after_media_paths = list_files(target_media, recursive=True)
    after_screen_paths = list_files(target_screens, recursive=True)

    new_media = {os.path.basename(p).lower() for p in after_media_paths} - before_media
    new_screens = {os.path.basename(p).lower() for p in after_screen_paths} - before_screens

    for path in after_media_paths:
        name = os.path.basename(path).lower()
        if name in new_media:
            records.append({"category": "media", "file_path": path})

    for path in after_screen_paths:
        name = os.path.basename(path).lower()
        if name in new_screens:
            records.append({"category": "screenshots", "file_path": path})

    return records


def _write_new_files_report(records: list[dict[str, str]], report_dir: str, report_format: str) -> None:
    """
    Write report of newly pulled files.
    """
    filename = _build_report_filename("PullNewMediaNewFiles", report_format)
    report_path = os.path.join(report_dir, filename)
    if report_format == "csv":
        save_csv(records, report_path, ["category", "file_path"])
    else:
        save_json({"records": records}, report_path)
    logging.info("New files report saved to %s", report_path)


def _build_report_filename(prefix: str, extension: str) -> str:
    """
    Build a timestamped report filename.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{prefix}_{timestamp}.{extension}"


if __name__ == "__main__":
    main()
