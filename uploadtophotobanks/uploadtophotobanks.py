#!/usr/bin/env python3
"""
Upload to Photobanks Script

Automatically uploads prepared media files to various photobank services via FTP/SFTP.
Supports Shutterstock, Pond5, 123RF, DepositPhotos, Alamy, Dreamstime, Adobe Stock, and CanStockPhoto.

This script reads the PhotoMedia.csv file, identifies files marked as "připraveno" (prepared)
for each photobank, and uploads them to the respective FTP/SFTP servers according to
each photobank's specific requirements and directory structure.
"""

import os
import sys
import argparse
import logging
from typing import Dict

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.utils import get_log_filename
from shared.logging_config import setup_logging

from uploadtophotobanksslib.constants import (
    DEFAULT_PHOTO_CSV,
    DEFAULT_PROCESSED_MEDIA_FOLDER,
    DEFAULT_EXPORT_DIR,
    DEFAULT_LOG_DIR,
    DEFAULT_UPLOAD_LOG_DIR,
    DEFAULT_CREDENTIALS_FILE,
    PHOTOBANK_CONFIGS
)
from uploadtophotobanksslib.uploader import PhotobankUploader
from uploadtophotobanksslib.credentials_manager import CredentialsManager
from shared.file_operations import save_csv


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Upload prepared media files to photobank services via FTP/SFTP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --shutterstock --pond5 --dry-run
  %(prog)s --all --credentials-file config/my_creds.json
  %(prog)s --alamy --photo-csv "L:\\PhotoMedia.csv"
  %(prog)s --setup-credentials

Supported photobanks:
  ShutterStock (FTPS), Pond5 (FTP), 123RF (FTP), DepositPhotos (FTP),
  Alamy (FTP), Dreamstime (FTP), AdobeStock (SFTP - requires qualification),
  CanStockPhoto (discontinued)

Security notes:
  - Environment variables are checked first for credentials (recommended)
  - Config files are used as fallback for missing photobanks only
  - Only Shutterstock and Adobe Stock use encrypted connections (FTPS/SFTP)
  - Other photobanks use plain FTP - use secure networks only
  - See ENV_SETUP.md for environment variable configuration
        """
    )

    # Basic parameters
    parser.add_argument("--media-folder", type=str, default=DEFAULT_PROCESSED_MEDIA_FOLDER,
                        help="Directory containing processed media files to upload")
    parser.add_argument("--export-dir", type=str, default=DEFAULT_EXPORT_DIR,
                        help="Directory containing exported CSV files")
    parser.add_argument("--log-dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--credentials-file", type=str, default=DEFAULT_CREDENTIALS_FILE,
                        help="Path to credentials JSON file")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate files and test connections without uploading")
    parser.add_argument("--export-upload-log", action="store_true",
                        help="Export per-file upload results to CSV")
    parser.add_argument("--upload-log-dir", type=str, default=DEFAULT_UPLOAD_LOG_DIR,
                        help="Directory for upload logs")

    # Photobank selection
    photobank_group = parser.add_argument_group("Photobank Selection")
    photobank_group.add_argument("--all", action="store_true",
                                 help="Upload to all configured photobanks")
    photobank_group.add_argument("--shutterstock", action="store_true",
                                 help="Upload to Shutterstock (FTPS)")
    photobank_group.add_argument("--pond5", action="store_true",
                                 help="Upload to Pond5 (FTP)")
    photobank_group.add_argument("--rf123", action="store_true",
                                 help="Upload to 123RF (FTP)")
    photobank_group.add_argument("--depositphotos", action="store_true",
                                 help="Upload to DepositPhotos (FTP)")
    photobank_group.add_argument("--alamy", action="store_true",
                                 help="Upload to Alamy (FTP)")
    photobank_group.add_argument("--dreamstime", action="store_true",
                                 help="Upload to Dreamstime (FTP)")
    photobank_group.add_argument("--adobestock", action="store_true",
                                 help="Upload to Adobe Stock (SFTP - requires qualification)")
    photobank_group.add_argument("--canstockphoto", action="store_true",
                                 help="CanStockPhoto (discontinued - will show info message)")

    # Utility commands
    utility_group = parser.add_argument_group("Utility Commands")
    utility_group.add_argument("--setup-credentials", action="store_true",
                               help="Interactively set up credentials")
    utility_group.add_argument("--test-connections", action="store_true",
                               help="Test connections to all configured photobanks")
    utility_group.add_argument("--list-uploadable", action="store_true",
                               help="List files ready for upload (no actual upload)")
    utility_group.add_argument("--create-credentials-template", action="store_true",
                               help="Create credentials template file")

    return parser.parse_args()


def main():
    """Main function."""
    args = parse_arguments()

    # Set up logging
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    logging.info("=" * 50)
    logging.info("Upload to Photobanks Script Started")
    logging.info("=" * 50)

    try:
        # Handle utility commands first
        if args.create_credentials_template:
            return handle_create_credentials_template(args)

        if args.setup_credentials:
            return handle_setup_credentials(args)

        # Initialize credentials manager (prioritizes environment variables)
        credentials_manager = CredentialsManager(args.credentials_file)

        # Show credentials source info
        show_credentials_info(credentials_manager)

        if args.test_connections:
            return handle_test_connections(credentials_manager)

        if args.list_uploadable:
            return handle_list_uploadable(args, credentials_manager)

        # Determine which photobanks to upload to
        selected_photobanks = get_selected_photobanks(args, credentials_manager)

        if not selected_photobanks:
            logging.error("No photobanks selected or no credentials available")
            print("Use --help to see available options")
            return 1

        # Validate input files
        if not validate_input_files(args):
            return 1

        # Initialize uploader
        all_credentials = credentials_manager.get_all_credentials()
        uploader = PhotobankUploader(all_credentials)

        # Display upload plan
        display_upload_plan(args, selected_photobanks, uploader)

        # Proceed directly with upload (no confirmation needed)

        # Perform upload
        results = uploader.upload_to_photobanks(
            args.media_folder,
            selected_photobanks,
            args.export_dir,
            args.dry_run
        )

        # Display results
        display_results(results, args.dry_run)

        if args.export_upload_log:
            _write_upload_log(results, args.upload_log_dir)

        # Determine exit code
        total_failures = sum(stats.get("failure", 0) + stats.get("error", 0)
                           for stats in results.values())
        return 1 if total_failures > 0 else 0

    except KeyboardInterrupt:
        logging.info("Upload interrupted by user")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def handle_create_credentials_template(args):
    """Handle creating credentials template."""
    credentials_manager = CredentialsManager()
    template_path = args.credentials_file or DEFAULT_CREDENTIALS_FILE

    if os.path.exists(template_path):
        overwrite = input(f"File {template_path} exists. Overwrite? [y/N]: ").strip().lower()
        if overwrite not in ['y', 'yes']:
            print("Template creation cancelled")
            return 0

    if credentials_manager.create_credentials_template(template_path):
        print(f"Credentials template created at: {template_path}")
        print("Please edit the file and add your actual credentials")
        return 0
    else:
        print("Failed to create credentials template")
        return 1


def handle_setup_credentials(args):
    """Handle interactive credentials setup."""
    credentials_manager = CredentialsManager(args.credentials_file)

    print("Available photobanks:")
    for i, photobank in enumerate(PHOTOBANK_CONFIGS.keys(), 1):
        print(f"{i:2d}. {photobank}")

    print(f"{len(PHOTOBANK_CONFIGS)+1:2d}. All photobanks")
    print(" 0. Exit")

    try:
        choice = input("\nSelect photobank (number): ").strip()
        choice_num = int(choice)

        if choice_num == 0:
            return 0

        photobanks = list(PHOTOBANK_CONFIGS.keys())

        if choice_num == len(PHOTOBANK_CONFIGS) + 1:
            # All photobanks
            selected = photobanks
        elif 1 <= choice_num <= len(PHOTOBANK_CONFIGS):
            # Single photobank
            selected = [photobanks[choice_num - 1]]
        else:
            print("Invalid choice")
            return 1

        # Set up credentials for selected photobanks
        for photobank in selected:
            print(f"\n--- Setting up {photobank} ---")
            if not credentials_manager.prompt_for_credentials(photobank):
                print(f"Failed to set up credentials for {photobank}")
                return 1

        print(f"\nCredentials saved to: {args.credentials_file}")
        return 0

    except (ValueError, KeyboardInterrupt):
        print("\nSetup cancelled")
        return 1


def handle_test_connections(credentials_manager):
    """Test connections to all configured photobanks."""
    photobanks = credentials_manager.list_photobanks()

    if not photobanks:
        print("No credentials configured. Use --setup-credentials first.")
        return 1

    print("Testing connections...")
    all_credentials = credentials_manager.get_all_credentials()
    uploader = PhotobankUploader(all_credentials)

    success_count = 0
    for photobank in photobanks:
        print(f"Testing {photobank}...", end=" ")
        if uploader.validate_credentials(photobank):
            print("OK Success")
            success_count += 1
        else:
            print("X Failed")

    print(f"\nConnection test complete: {success_count}/{len(photobanks)} successful")
    return 0 if success_count == len(photobanks) else 1


def handle_list_uploadable(args, credentials_manager):
    """List files ready for upload without uploading."""
    photobanks = credentials_manager.list_photobanks()

    if not photobanks:
        print("No credentials configured. Use --setup-credentials first.")
        return 1

    all_credentials = credentials_manager.get_all_credentials()
    uploader = PhotobankUploader(all_credentials)

    print("Files ready for upload:")
    total_files = 0

    for photobank in photobanks:
        count = uploader.get_uploadable_files_count(args.photo_csv, photobank)
        print(f"{photobank:15}: {count:4d} files")
        total_files += count

    print(f"{'Total':15}: {total_files:4d} files")
    return 0


def get_selected_photobanks(args, credentials_manager):
    """Determine which photobanks to upload to."""
    available_photobanks = credentials_manager.list_photobanks()

    if args.all:
        return available_photobanks

    selected = []
    if args.shutterstock and "ShutterStock" in available_photobanks:
        selected.append("ShutterStock")
    if args.pond5 and "Pond5" in available_photobanks:
        selected.append("Pond5")
    if args.rf123 and "123RF" in available_photobanks:
        selected.append("123RF")
    if args.depositphotos and "DepositPhotos" in available_photobanks:
        selected.append("DepositPhotos")
    if args.alamy and "Alamy" in available_photobanks:
        selected.append("Alamy")
    if args.dreamstime and "Dreamstime" in available_photobanks:
        selected.append("Dreamstime")
    if args.adobestock and "AdobeStock" in available_photobanks:
        selected.append("AdobeStock")
    if args.canstockphoto:
        selected.append("CanStockPhoto")

    return selected


def validate_input_files(args):
    """Validate that required input files exist."""
    if not os.path.exists(args.media_folder):
        logging.error(f"Media folder not found: {args.media_folder}")
        logging.error("Please run createbatch first to process media files")
        return False

    if not os.path.exists(args.export_dir):
        logging.error(f"Export directory not found: {args.export_dir}")
        logging.error("Please run exportpreparedmedia first")
        return False

    return True


def display_upload_plan(args, photobanks, uploader):
    """Display the upload plan."""
    print("\nUpload Plan:")
    print("=" * 40)
    print(f"Media Folder: {args.media_folder}")
    print(f"Export Dir: {args.export_dir}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPLOAD'}")
    print()

    # Count media files per photobank
    try:
        media_files = uploader._scan_media_folder(args.media_folder)
        total_files = len(media_files)

        for photobank in photobanks:
            compatible_files = uploader._filter_files_for_photobank(media_files, photobank)
            count = len(compatible_files)
            protocol = PHOTOBANK_CONFIGS[photobank]["protocol"].upper()
            print(f"{photobank:15} ({protocol:4}): {count:4d} files")
    except Exception as e:
        logging.error(f"Failed to scan media files: {e}")
        total_files = 0

    print("-" * 40)
    print(f"{'Total':20}: {total_files:4d} files")
    print()


def display_results(results, dry_run):
    """Display upload results."""
    mode = "DRY RUN" if dry_run else "UPLOAD"
    print(f"\n{mode} Results:")
    print("=" * 50)

    total_success = 0
    total_failure = 0
    total_skipped = 0
    total_error = 0

    for photobank, stats in results.items():
        success = stats.get("success", 0)
        failure = stats.get("failure", 0)
        skipped = stats.get("skipped", 0)
        error = stats.get("error", 0)

        total_success += success
        total_failure += failure
        total_skipped += skipped
        total_error += error

        status = "OK" if (success > 0 and failure == 0 and error == 0) else "X" if (failure > 0 or error > 0) else "-"
        print(f"{status} {photobank:15}: {success:3d} success, {failure:3d} failed, {skipped:3d} skipped, {error:3d} error")

    print("-" * 50)
    print(f"  {'Total':15}: {total_success:3d} success, {total_failure:3d} failed, {total_skipped:3d} skipped, {total_error:3d} error")

    if not dry_run and total_success > 0:
        print(f"\n{total_success} files uploaded successfully!")
        print("Don't forget to check photobank portals for post-upload processing.")


def show_credentials_info(credentials_manager):
    """Show information about credentials sources."""
    photobanks = credentials_manager.list_photobanks()

    if not photobanks:
        print("No credentials found. Set environment variables or use --setup-credentials.")
        print("See ENV_SETUP.md for environment variable configuration.")
        return

    # This is a simple approach - in a more sophisticated version,
    # we could track which credentials came from env vs file
    logging.info(f"Credentials loaded for {len(photobanks)} photobank(s)")
    if logging.getLogger().level <= logging.DEBUG:
        print("Credentials source priority: 1) Environment variables, 2) Config file")
        print(f"Photobanks configured: {', '.join(photobanks)}")


def _write_upload_log(results: Dict[str, Dict[str, int]], upload_log_dir: str) -> None:
    """
    Write per-file upload results to CSV.
    """
    log_records: list[dict[str, str]] = []
    for photobank, stats in results.items():
        files = stats.get("files", [])
        for record in files:
            log_records.append({
                "photobank": record.get("photobank", photobank),
                "filename": record.get("filename", ""),
                "status": record.get("status", ""),
                "message": record.get("message", "")
            })

    if not log_records:
        return

    if not os.path.exists(upload_log_dir):
        os.makedirs(upload_log_dir, exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(upload_log_dir, f"UploadLog_{timestamp}.csv")
    save_csv(log_records, log_path)


if __name__ == "__main__":
    sys.exit(main())
