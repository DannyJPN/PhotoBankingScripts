import logging
import os
import sys
import tempfile

from PyQt5.QtGui import QImage, QPixmap

from removealreadysortedoutlib.constants import JPEG_EXTENSIONS

# Global flag to track if rawpy is available
RAWPY_AVAILABLE = False
PILLOW_AVAILABLE = False

# Try to import rawpy and PIL
try:
    import rawpy

    RAWPY_AVAILABLE = True
except ImportError:
    logging.warning("rawpy library not available. RAW file preview will be limited.")

try:
    from PIL import Image

    PILLOW_AVAILABLE = True
except ImportError:
    logging.warning("Pillow library not available. Image conversion will be limited.")


def convert_raw_to_preview(raw_path: str) -> tuple[QPixmap, str] | None:
    """
    Convert a RAW image file to a QPixmap for preview.

    Args:
        raw_path: Path to the RAW image file

    Returns:
        Tuple containing (QPixmap, temp_file_path) if successful, None otherwise.
        The caller is responsible for cleaning up the temporary file.
    """
    logging.info(f"Attempting to convert RAW file to preview: {raw_path}")

    if not os.path.exists(raw_path):
        logging.error(f"RAW file does not exist: {raw_path}")
        return None

    # Create a temporary file for the converted image
    temp_file = None

    # Suppress stderr to avoid TIFF warnings
    original_stderr = sys.stderr
    try:
        # Redirect stderr to suppress warnings
        with open(os.devnull, "w") as devnull:
            sys.stderr = devnull

            # Method 1: Use rawpy if available
            if RAWPY_AVAILABLE and PILLOW_AVAILABLE:
                try:
                    # Create a temporary file for the JPEG
                    fd, temp_path = tempfile.mkstemp(suffix=".jpg")
                    os.close(fd)
                    temp_file = temp_path

                    # Open the RAW file and convert to RGB
                    with rawpy.imread(raw_path) as raw:
                        # Get the postprocessed image
                        rgb = raw.postprocess(use_camera_wb=True, half_size=True, no_auto_bright=False)

                    # Convert to PIL Image and save as JPEG
                    img = Image.fromarray(rgb)
                    img.save(temp_path, format="JPEG", quality=85)

                    # Load the JPEG into a QPixmap
                    pixmap = QPixmap(temp_path)
                    if not pixmap.isNull():
                        logging.info(f"Successfully converted RAW file to preview using rawpy: {raw_path}")
                        return pixmap, temp_path
                except Exception as e:
                    logging.debug(f"rawpy conversion failed for {raw_path}: {e}")

            # Method 2: Try to use QImage directly (might work for some RAW formats)
            try:
                image = QImage(raw_path)
                if not image.isNull() and image.width() > 0 and image.height() > 0:
                    pixmap = QPixmap.fromImage(image)
                    logging.info(f"Successfully loaded RAW file directly with QImage: {raw_path}")
                    return pixmap, None  # No temp file to clean up
            except Exception as e:
                logging.debug(f"QImage failed to load RAW file {raw_path}: {e}")

            # Method 3: Look for a JPEG preview with the same name
            try:
                # Check if there's a JPEG with the same name
                base_path = os.path.splitext(raw_path)[0]
                for ext in JPEG_EXTENSIONS:
                    jpeg_path = base_path + ext
                    if os.path.exists(jpeg_path):
                        # Load the JPEG preview
                        pixmap = QPixmap(jpeg_path)
                        if not pixmap.isNull():
                            logging.info(f"Successfully loaded JPEG preview for RAW file: {raw_path} -> {jpeg_path}")
                            return pixmap, None  # No temp file to clean up
            except Exception as e:
                logging.debug(f"Failed to find JPEG preview for {raw_path}: {e}")

    except Exception as e:
        logging.error(f"Error converting RAW file {raw_path}: {e}")
    finally:
        # Restore stderr
        sys.stderr = original_stderr

        # If we failed but created a temp file, clean it up
        if temp_file and not os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                temp_file = None
            except:
                pass

    return None


def cleanup_temp_file(temp_path: str | None) -> None:
    """
    Clean up a temporary file if it exists.

    Args:
        temp_path: Path to the temporary file
    """
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception as e:
            logging.debug(f"Failed to remove temporary file {temp_path}: {e}")
