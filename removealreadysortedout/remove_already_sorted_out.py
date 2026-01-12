import os
import argparse
import logging
from datetime import datetime
from tqdm import tqdm

from shared.utils import get_log_filename
from shared.file_operations import list_files, ensure_directory, unify_duplicate_files, save_csv, save_json
from shared.logging_config import setup_logging

from removealreadysortedoutlib.constants import (
    DEFAULT_UNSORTED_FOLDER,
    DEFAULT_TARGET_FOLDER,
    DEFAULT_LOG_DIR,
    DEFAULT_REPORT_DIR,
    DEFAULT_REPORT_FORMAT,
    PREFIXES_TO_NORMALIZE,
)

from removealreadysortedoutlib.removal_operations import (
    get_target_files_map,
    find_duplicates,
    handle_duplicate,
    remove_desktop_ini,
    should_replace_file
)

from removealreadysortedoutlib.renaming import (
    replace_in_filenames,
    normalize_indexed_filenames
)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Remove files from unsorted folder that already exist in target folder."
    )
    parser.add_argument("--unsorted_folder", type=str, default=DEFAULT_UNSORTED_FOLDER,
                        help="Source folder with unsorted files")
    parser.add_argument("--target_folder", type=str, default=DEFAULT_TARGET_FOLDER,
                        help="Target folder with sorted files")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite files with different sizes")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--index_prefix", type=str, default="PICT", 
                        help="Prefix for indexed filenames")
    parser.add_argument("--index_width", type=int, default=4, 
                        help="Width of numeric suffix")
    parser.add_argument("--index_max", type=int, default=9999, 
                        help="Max index number to scan")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview duplicate removals without changes")
    parser.add_argument("--report-dir", type=str, default=DEFAULT_REPORT_DIR,
                        help="Directory for dry-run report")
    parser.add_argument("--report-format", type=str, default=DEFAULT_REPORT_FORMAT,
                        choices=["csv", "json"], help="Report format: csv or json")
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)
    
    logging.info("Starting RemoveAlreadySortedOut process")
    logging.info(f"Unsorted folder: {args.unsorted_folder}")
    logging.info(f"Target folder: {args.target_folder}")
    logging.info(f"Overwrite mode: {args.overwrite}")
    
    # Remove desktop.ini if it exists
    remove_desktop_ini(args.unsorted_folder)
    
    # Step 1: Unify duplicate files in both folders (same as pullnew)
    logging.info("Step 1: Unifying duplicate files...")
    unify_duplicate_files(args.unsorted_folder, recursive=True)
    unify_duplicate_files(args.target_folder, recursive=True)
    
    # Step 2: Generic filename replacements (_NIK -> NIK_ by default)
    logging.info("Step 2: Replacing filename patterns...")
    replace_in_filenames(args.unsorted_folder, "_NIK", "NIK_", recursive=True)
    replace_in_filenames(args.target_folder, "_NIK", "NIK_", recursive=True)
    
    # Step 3: Normalize indexed filenames in unsorted vs target
    logging.info("Step 3: Normalizing indexed filenames...")
    for prefix in PREFIXES_TO_NORMALIZE:
        normalize_indexed_filenames(
            source_folder=args.unsorted_folder,
            reference_folder=args.target_folder,
            prefix=prefix,
            width=args.index_width,
            max_number=args.index_max,
        )
    
    # Step 4: Get list of files from unsorted folder (after preprocessing)
    logging.info("Step 4: Listing files in unsorted folder...")
    unsorted_files = list_files(args.unsorted_folder, recursive=True)
    logging.info(f"Found {len(unsorted_files)} files in unsorted folder")
    
    # Get map of files in target folder
    logging.info("Building map of files in target folder...")
    target_files_map = get_target_files_map(args.target_folder)
    logging.info(f"Found {len(target_files_map)} unique filenames in target folder")
    
    # Find duplicates
    logging.info("Finding duplicates...")
    duplicates = find_duplicates(unsorted_files, target_files_map)
    logging.info(f"Found {len(duplicates)} files that exist in both folders")
    
    if args.dry_run:
        report_records = _build_dry_run_report(duplicates, args.overwrite)
        _write_dry_run_report(report_records, args.report_dir, args.report_format)
        logging.info("Dry-run completed, no files were modified")
        return

    # Process duplicates
    logging.info("Processing duplicates...")
    with tqdm(total=len(duplicates), desc="Removing duplicates", unit="files") as pbar:
        for source_path, target_paths in duplicates.items():
            handle_duplicate(source_path, target_paths, args.overwrite, log_file)
            pbar.update(1)
    
    logging.info("RemoveAlreadySortedOut process completed successfully")

def _build_dry_run_report(duplicates: dict[str, list[str]], overwrite: bool) -> list[dict[str, str]]:
    """
    Build a dry-run report for duplicates.
    """
    records: list[dict[str, str]] = []
    for source_path, target_paths in duplicates.items():
        action = _determine_action(source_path, target_paths, overwrite)
        records.append({
            "source_path": source_path,
            "target_paths": "|".join(target_paths),
            "action": action
        })
    return records


def _determine_action(source_path: str, target_paths: list[str], overwrite: bool) -> str:
    """
    Determine action that would be taken for a duplicate.
    """
    for target_path in target_paths:
        if not os.path.exists(target_path):
            continue
        if should_replace_file(source_path, target_path):
            return "replace" if overwrite else "skip_replace"
        return "remove_source"
    return "skip_missing_target"


def _write_dry_run_report(records: list[dict[str, str]], report_dir: str, report_format: str) -> None:
    """
    Write dry-run report to CSV or JSON.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"RemoveAlreadySortedOutDryRun_{timestamp}.{report_format}"
    report_path = os.path.join(report_dir, filename)
    if report_format == "csv":
        save_csv(records, report_path, ["source_path", "target_paths", "action"])
    else:
        save_json({"records": records}, report_path)
    logging.info("Dry-run report saved to %s", report_path)


if __name__ == "__main__":
    main()
