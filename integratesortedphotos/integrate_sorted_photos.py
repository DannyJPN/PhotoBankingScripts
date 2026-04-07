import os
import logging
import argparse
from shared.logging_config import setup_logging
from integratesortedphotoslib.constants import DEFAULT_SORTED_FOLDER, DEFAULT_TARGET_FOLDER, DEFAULT_LOG_DIR, DEFAULT_REPORT_DIR, DEFAULT_REPORT_FORMAT
from integratesortedphotoslib.copy_files import copy_files_with_preserved_dates
from shared.utils import get_log_filename
from shared.file_operations import ensure_directory, save_csv, save_json

def parse_arguments():
    parser = argparse.ArgumentParser(description="Integrate sorted photos from one directory to another.")
    parser.add_argument('--sortedFolder', type=str, nargs='?', default=DEFAULT_SORTED_FOLDER, help="Path to the sorted folder.")
    parser.add_argument('--targetFolder', type=str, nargs='?', default=DEFAULT_TARGET_FOLDER, help="Path to the target folder.")
    parser.add_argument('--log_dir', type=str, default=DEFAULT_LOG_DIR, help="Directory for log files")
    parser.add_argument('--debug', action='store_true', help="Enable debug mode.")
    parser.add_argument('--export-report', action='store_true', help="Export integration report")
    parser.add_argument('--report-dir', type=str, default=DEFAULT_REPORT_DIR, help="Directory for report output")
    parser.add_argument('--report-format', type=str, default=DEFAULT_REPORT_FORMAT, choices=["csv", "json"])
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)
    
    logging.info("Starting integrate sorted photos")
    logging.info(f"SortedFolder: {args.sortedFolder}")
    logging.info(f"TargetFolder: {args.targetFolder}")

    # Ensure the paths are valid
    if not os.path.exists(args.sortedFolder):
        logging.error(f"SortedFolder does not exist: {args.sortedFolder}")
        return

    # Call the copy function
    stats = copy_files_with_preserved_dates(args.sortedFolder, args.targetFolder)
    if args.export_report:
        _write_report(stats, args.report_dir, args.report_format)

def _write_report(stats: dict[str, int], report_dir: str, report_format: str) -> None:
    """
    Write integration report to CSV or JSON.
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = os.path.join(report_dir, f"IntegrateSortedPhotosReport_{timestamp}.{report_format}")
    records = [{"metric": key, "count": str(value)} for key, value in stats.items()]
    if report_format == "csv":
        save_csv(records, report_path, ["metric", "count"])
    else:
        save_json({"metrics": records}, report_path)


if __name__ == '__main__':
    main()
