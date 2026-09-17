"""
Main uploader logic for photobank files.
"""
import os
import logging
from typing import List, Dict, Optional, Tuple
from tqdm import tqdm

from uploadtophotobanksslib.constants import (
    PHOTOBANK_CONFIGS,
    COL_FILE,
    COL_PATH,
    VALID_STATUS_FOR_UPLOAD,
    UPLOAD_SUCCESS,
    UPLOAD_FAILURE,
    UPLOAD_SKIPPED,
    get_status_column
)
from uploadtophotobanksslib.connection_manager import ConnectionManager
from uploadtophotobanksslib.file_validator import FileValidator
from shared.file_operations import load_csv, save_csv


class PhotobankUploader:
    """Main uploader class for photobank files."""

    def __init__(self, credentials: Dict[str, Dict[str, str]]):
        """
        Initialize uploader with credentials.

        Args:
            credentials: Dict with photobank names as keys and credential dicts as values
                        e.g., {"ShutterStock": {"username": "user", "password": "pass"}}
        """
        self.credentials = credentials
        self.connection_manager = ConnectionManager()
        self.file_validator = FileValidator()

    def upload_to_photobanks(
        self,
        media_folder: str,
        photobanks: List[str],
        export_dir: str,
        dry_run: bool = False
    ) -> Dict[str, Dict[str, int]]:
        """
        Upload files to specified photobanks.

        Args:
            media_folder: Directory containing processed media files to upload
            photobanks: List of photobank names to upload to
            export_dir: Directory containing exported CSV files
            dry_run: If True, only validate files without uploading

        Returns:
            Dict with upload statistics per photobank
        """
        logging.info(f"Starting upload to photobanks: {', '.join(photobanks)}")

        # Scan media folder for files to upload
        try:
            media_files = self._scan_media_folder(media_folder)
            logging.info(f"Found {len(media_files)} media files in {media_folder}")
        except Exception as e:
            logging.error(f"Failed to scan media folder {media_folder}: {e}")
            return {}

        if not media_files:
            logging.warning("No media files found to upload")
            return {}

        results = {}

        for photobank in photobanks:
            logging.info(f"Processing photobank: {photobank}")
            results[photobank] = self._upload_to_photobank(
                photobank, media_files, export_dir, dry_run
            )

        # Disconnect all connections
        self.connection_manager.disconnect_all()

        return results

    def _scan_media_folder(self, media_folder: str) -> List[str]:
        """Scan media folder for files to upload."""
        if not os.path.exists(media_folder):
            raise FileNotFoundError(f"Media folder not found: {media_folder}")

        media_files = []
        supported_extensions = set()

        # Collect all supported extensions from photobank configs
        for config in PHOTOBANK_CONFIGS.values():
            supported_extensions.update(config.get("supported_formats", []))

        # Scan folder for media files
        for filename in os.listdir(media_folder):
            file_path = os.path.join(media_folder, filename)

            # Skip directories
            if os.path.isdir(file_path):
                continue

            # Check if file has supported extension
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in supported_extensions:
                media_files.append(file_path)
                logging.debug(f"Found media file: {file_path}")

        return sorted(media_files)

    def _upload_to_photobank(
        self,
        photobank: str,
        media_files: List[str],
        export_dir: str,
        dry_run: bool
    ) -> Dict[str, int]:
        """Upload files to a specific photobank."""

        if photobank not in PHOTOBANK_CONFIGS:
            logging.error(f"Unsupported photobank: {photobank}")
            return {"error": 1}

        config = PHOTOBANK_CONFIGS[photobank]

        # Handle discontinued photobanks
        if config.get("discontinued", False):
            message = config.get("discontinuation_message", f"{photobank} has been discontinued")
            logging.warning(f"DISCONTINUED: {message}")
            print(f"INFO: {photobank}: {message}")
            return {"skipped": len(media_files), "discontinuation_notice": 1}

        if photobank not in self.credentials:
            logging.error(f"No credentials provided for {photobank}")
            return {"error": 1}

        # Filter files supported by this photobank
        uploadable_files = self._filter_files_for_photobank(media_files, photobank)
        logging.info(f"Found {len(uploadable_files)} files compatible with {photobank}")

        if not uploadable_files:
            return {"skipped": 0}

        # Check if exported CSV exists (try both formats)
        export_csv_path = os.path.join(export_dir, f"{photobank}Output.csv")
        export_csv_path_alt = os.path.join(export_dir, f"CSV_{photobank}.csv")

        if os.path.exists(export_csv_path):
            csv_path_to_use = export_csv_path
        elif os.path.exists(export_csv_path_alt):
            csv_path_to_use = export_csv_path_alt
            logging.info(f"Using alternative CSV format: {export_csv_path_alt}")
        else:
            logging.warning(f"Export CSV not found for {photobank}")
            logging.warning(f"Tried: {export_csv_path} and {export_csv_path_alt}")
            logging.warning("Please run exportpreparedmedia first")
            return {"error": len(uploadable_files)}

        # Load export CSV to validate files are prepared for this photobank
        try:
            export_records = load_csv(csv_path_to_use)
            export_filenames = {os.path.basename(record.get("Filename", "")) for record in export_records}
            logging.info(f"Loaded {len(export_records)} exported records for {photobank}")
        except Exception as e:
            logging.error(f"Failed to load export CSV {csv_path_to_use}: {e}")
            return {"error": len(uploadable_files)}

        stats = {"success": 0, "failure": 0, "skipped": 0}
        file_results: List[Dict[str, str]] = []

        if dry_run:
            logging.info("DRY RUN MODE - No files will be uploaded")

        # Get connection
        if not dry_run:
            connection = self.connection_manager.get_connection(photobank, self.credentials[photobank])
            if not connection:
                logging.error(f"Failed to connect to {photobank}")
                return {"error": len(uploadable_files)}

        # Process each file
        for file_path in tqdm(uploadable_files, desc=f"Uploading to {photobank}"):
            filename = os.path.basename(file_path)

            # Note: CSV files are optional - upload all compatible files from media folder
            logging.debug(f"Processing file: {filename}")

            # Validate file
            if not self.file_validator.validate_file_for_photobank(file_path, photobank):
                logging.error(f"File validation failed for {filename}")
                stats["failure"] += 1
                file_results.append({
                    "photobank": photobank,
                    "filename": filename,
                    "status": "failure",
                    "message": "validation_failed"
                })
                continue

            if dry_run:
                logging.info(f"[DRY RUN] Would upload: {filename}")
                stats["success"] += 1
                file_results.append({
                    "photobank": photobank,
                    "filename": filename,
                    "status": "success",
                    "message": "dry_run"
                })
                continue

            # Upload file
            success = self._upload_single_file(connection, file_path, filename, photobank)

            if success:
                stats["success"] += 1
                logging.info(f"Successfully uploaded {filename} to {photobank}")
                file_results.append({
                    "photobank": photobank,
                    "filename": filename,
                    "status": "success",
                    "message": ""
                })
            else:
                stats["failure"] += 1
                logging.error(f"Failed to upload {filename} to {photobank}")
                file_results.append({
                    "photobank": photobank,
                    "filename": filename,
                    "status": "failure",
                    "message": "upload_failed"
                })

        stats["files"] = file_results
        logging.info(f"Upload to {photobank} completed: {stats}")
        return stats

    def _filter_files_for_photobank(self, media_files: List[str], photobank: str) -> List[str]:
        """Filter media files that are supported by the specified photobank."""
        config = PHOTOBANK_CONFIGS[photobank]
        supported_formats = config.get("supported_formats", [])

        compatible_files = []
        for file_path in media_files:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in supported_formats:
                compatible_files.append(file_path)
            else:
                logging.debug(f"File {file_path} not supported by {photobank} (extension: {file_ext})")

        return compatible_files

    def _filter_uploadable_files(self, media_records: List[Dict[str, str]], status_col: str) -> List[Dict[str, str]]:
        """Filter files that are ready for upload."""
        uploadable = []

        for record in media_records:
            # Check if file has the required status
            current_status = record.get(status_col, "").strip()

            # Only upload files that are marked as prepared and not already uploaded
            if current_status == VALID_STATUS_FOR_UPLOAD:
                # Check if file exists
                file_path = record.get(COL_PATH, "")
                if not file_path or not os.path.exists(file_path):
                    logging.warning(f"File not found: {record.get(COL_FILE, 'Unknown')}")
                    continue

                uploadable.append(record)

        return uploadable

    def _upload_single_file(
        self,
        connection,
        local_path: str,
        filename: str,
        photobank: str
    ) -> bool:
        """Upload a single file to photobank."""

        config = PHOTOBANK_CONFIGS[photobank]

        # Special handling for 123RF with dynamic server switching
        if photobank == "123RF" and hasattr(connection, 'upload_file_with_switch'):
            return connection.upload_file_with_switch(local_path, filename)

        # Standard upload process for other photobanks
        # Determine target directory
        target_dir = self._get_target_directory(local_path, photobank)

        # Change to target directory if needed
        if target_dir != "/" and hasattr(connection, 'change_directory'):
            if not connection.change_directory(target_dir):
                logging.error(f"Failed to change to directory {target_dir}")
                return False

        # Upload the file
        return connection.upload_file(local_path, filename)

    def _get_target_directory(self, file_path: str, photobank: str) -> str:
        """Determine the target directory for upload based on file type and photobank rules."""

        config = PHOTOBANK_CONFIGS[photobank]
        file_ext = os.path.splitext(file_path)[1].lower()

        # Handle photobanks with multiple directories
        if "directories" in config:
            directories = config["directories"]

            if photobank == "Alamy":
                # Alamy logic: vectors go to /Vectors, everything else to /Stock
                if file_ext in ['.eps', '.ai']:
                    return directories.get("vectors", "/")
                else:
                    return directories.get("stock", "/")

            elif photobank == "Dreamstime":
                # Dreamstime logic based on file type
                if file_ext in ['.mp4', '.mov', '.avi']:
                    return directories.get("video", "/")
                elif file_ext in ['.wav', '.mp3', '.flac']:
                    return directories.get("audio", "/")
                elif file_ext in ['.eps', '.ai'] or 'RAW' in file_path.upper():
                    return directories.get("additional", "/")
                else:
                    return directories.get("photos", "/")

        # Default directory or root
        return config.get("directory", "/")

    def _get_current_datetime(self) -> str:
        """Get current datetime in the format used by the system."""
        from datetime import datetime
        return datetime.now().strftime("%d.%m.%Y %H:%M")

    def get_uploadable_files_count(self, csv_path: str, photobank: str) -> int:
        """Get count of files ready for upload to specific photobank."""
        try:
            media_records = load_csv(csv_path)
            status_col = get_status_column(photobank)
            uploadable = self._filter_uploadable_files(media_records, status_col)
            return len(uploadable)
        except Exception as e:
            logging.error(f"Failed to count uploadable files: {e}")
            return 0

    def validate_credentials(self, photobank: str) -> bool:
        """Test connection to photobank to validate credentials."""
        if photobank not in self.credentials:
            return False

        connection = self.connection_manager.get_connection(photobank, self.credentials[photobank])
        if connection:
            # Special handling for 123RF - it successfully connected during get_connection
            if photobank == "123RF" and hasattr(connection, 'current_host'):
                # RF123Connection successfully connected if it got through get_connection
                self.connection_manager.disconnect(photobank)
                return True

            # Standard test for other photobanks
            if connection.is_connected():
                self.connection_manager.disconnect(photobank)
                return True
        return False
