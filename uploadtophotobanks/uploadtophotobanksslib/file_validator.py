"""
File validator for photobank uploads.
"""
import os
import logging
from typing import Dict, List, Optional
from PIL import Image

from uploadtophotobanksslib.constants import PHOTOBANK_CONFIGS


class FileValidator:
    """Validates files against photobank requirements."""

    def __init__(self):
        self.image_cache = {}

    def validate_file_for_photobank(self, file_path: str, photobank: str) -> bool:
        """
        Validate if file meets photobank requirements.

        Args:
            file_path: Path to the file to validate
            photobank: Name of the photobank

        Returns:
            True if file meets requirements, False otherwise
        """
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return False

        config = PHOTOBANK_CONFIGS.get(photobank)
        if not config:
            logging.error(f"No configuration found for photobank: {photobank}")
            return False

        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        supported_formats = config.get("supported_formats", [])

        if file_ext not in supported_formats:
            logging.error(f"File format {file_ext} not supported by {photobank}")
            return False

        # Check file size
        file_size = os.path.getsize(file_path)
        max_sizes = config.get("max_file_size", {})

        if max_sizes:
            # Get format-specific limit or default
            format_key = file_ext[1:]  # Remove the dot
            max_size = max_sizes.get(format_key, max_sizes.get("default", float('inf')))

            if file_size > max_size:
                logging.error(f"File {file_path} size {file_size} exceeds limit {max_size} for {photobank}")
                return False

        # Image-specific validation
        if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
            return self._validate_image(file_path, photobank, config)

        # Video-specific validation
        if file_ext in ['.mp4', '.mov', '.avi', '.wmv']:
            return self._validate_video(file_path, photobank, config)

        # Vector-specific validation
        if file_ext in ['.eps', '.ai', '.svg']:
            return self._validate_vector(file_path, photobank, config)

        # Audio-specific validation
        if file_ext in ['.wav', '.mp3', '.flac']:
            return self._validate_audio(file_path, photobank, config)

        logging.info(f"File {file_path} passed basic validation for {photobank}")
        return True

    def _validate_image(self, file_path: str, photobank: str, config: Dict) -> bool:
        """Validate image file."""
        try:
            # Use cached image info if available
            if file_path not in self.image_cache:
                with Image.open(file_path) as img:
                    self.image_cache[file_path] = {
                        "width": img.width,
                        "height": img.height,
                        "mode": img.mode,
                        "format": img.format
                    }

            img_info = self.image_cache[file_path]

            # Note: Size validations removed - let FTP server handle size requirements

            # Check color mode for JPEG
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                if img_info["mode"] not in ["RGB", "L"]:  # L is grayscale
                    logging.error(f"Image {file_path} has unsupported color mode {img_info['mode']} for {photobank}")
                    return False

            # Note: Photobank-specific size checks removed - let servers validate requirements

            logging.debug(f"Image {file_path} validated successfully for {photobank}")
            return True

        except Exception as e:
            logging.error(f"Failed to validate image {file_path}: {e}")
            return False

    def _validate_video(self, file_path: str, photobank: str, config: Dict) -> bool:
        """Validate video file."""
        try:
            # Basic file size check (already done in main validation)
            file_size = os.path.getsize(file_path)

            # Photobank-specific video requirements
            if photobank == "ShutterStock":
                # Shutterstock: 5-60 seconds, max 4GB
                max_size = 4 * 1024 * 1024 * 1024  # 4GB
                if file_size > max_size:
                    logging.error(f"Video {file_path} exceeds Shutterstock 4GB limit")
                    return False

            elif photobank == "123RF":
                # 123RF: max 120 seconds, max 4GB
                max_size = 4 * 1024 * 1024 * 1024  # 4GB
                if file_size > max_size:
                    logging.error(f"Video {file_path} exceeds 123RF 4GB limit")
                    return False

            elif photobank == "Pond5":
                # Pond5: max 60 seconds, max 4GB
                max_size = 4 * 1024 * 1024 * 1024  # 4GB
                if file_size > max_size:
                    logging.error(f"Video {file_path} exceeds Pond5 4GB limit")
                    return False

            logging.debug(f"Video {file_path} validated successfully for {photobank}")
            return True

        except Exception as e:
            logging.error(f"Failed to validate video {file_path}: {e}")
            return False

    def _validate_vector(self, file_path: str, photobank: str, config: Dict) -> bool:
        """Validate vector file."""
        try:
            file_size = os.path.getsize(file_path)

            # Basic size checks
            if photobank == "ShutterStock":
                # Shutterstock: max 100MB for EPS
                max_size = 100 * 1024 * 1024  # 100MB
                if file_size > max_size:
                    logging.error(f"Vector {file_path} exceeds Shutterstock 100MB limit")
                    return False

            elif photobank == "AdobeStock":
                # Adobe Stock: max 45MB for AI/EPS
                max_size = 45 * 1024 * 1024  # 45MB
                if file_size > max_size:
                    logging.error(f"Vector {file_path} exceeds Adobe Stock 45MB limit")
                    return False

            # Check for required JPEG companion (for some photobanks)
            if photobank in ["123RF", "DepositPhotos", "Alamy"]:
                # These photobanks may require JPEG preview with vectors
                base_name = os.path.splitext(file_path)[0]
                jpeg_path = base_name + ".jpg"
                if not os.path.exists(jpeg_path):
                    logging.warning(f"Vector {file_path} should have companion JPEG for {photobank}")
                    # Don't fail validation, just warn

            logging.debug(f"Vector {file_path} validated successfully for {photobank}")
            return True

        except Exception as e:
            logging.error(f"Failed to validate vector {file_path}: {e}")
            return False

    def _validate_audio(self, file_path: str, photobank: str, config: Dict) -> bool:
        """Validate audio file."""
        try:
            file_size = os.path.getsize(file_path)

            # Photobank-specific audio requirements
            if photobank == "Pond5":
                # Pond5: max 10 minutes (approximately 170MB for high quality)
                max_size = 200 * 1024 * 1024  # 200MB to be safe
                if file_size > max_size:
                    logging.error(f"Audio {file_path} exceeds Pond5 size limit")
                    return False

            elif photobank == "123RF":
                # 123RF accepts audio but no specific limits documented
                max_size = 200 * 1024 * 1024  # 200MB conservative limit
                if file_size > max_size:
                    logging.error(f"Audio {file_path} exceeds 123RF size limit")
                    return False

            logging.debug(f"Audio {file_path} validated successfully for {photobank}")
            return True

        except Exception as e:
            logging.error(f"Failed to validate audio {file_path}: {e}")
            return False

    def clear_cache(self) -> None:
        """Clear the image info cache."""
        self.image_cache.clear()

    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """Get cached file information."""
        return self.image_cache.get(file_path)