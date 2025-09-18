"""
Alternative versions generator for photobank media files.
Creates processed variants (B&W, negative, sharpened, misty, blurred) and format conversions.
"""
from typing import List, Tuple, Dict, Optional
import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import logging
from pathlib import Path

from .constants import (
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS,
    ALTERNATIVE_EDIT_TAGS, ALTERNATIVE_FORMATS,
    ORIGINAL_YES, ORIGINAL_NO
)

logger = logging.getLogger(__name__)


class AlternativeGenerator:
    """Generator for alternative versions and format conversions of media files."""

    def __init__(self, enabled_alternatives: Optional[List[str]] = None, enabled_formats: Optional[List[str]] = None):
        """
        Initialize alternative generator.

        Args:
            enabled_alternatives: List of alternative edit types to generate.
                                If None, generates all available alternatives.
                                If empty list [], generates no alternatives.
            enabled_formats: List of additional formats to generate.
                           If None, generates all available formats.
                           If empty list [], generates no format conversions.
        """
        self.enabled_alternatives = enabled_alternatives if enabled_alternatives is not None else list(ALTERNATIVE_EDIT_TAGS.keys())
        self.enabled_formats = enabled_formats if enabled_formats is not None else ALTERNATIVE_FORMATS
        logger.info(f"Alternative generator initialized - Effects: {self.enabled_alternatives}, Formats: {self.enabled_formats}")

    def generate_all_versions(self, source_file: str, target_dir: str, edited_dir: str) -> List[Dict[str, str]]:
        """
        Generate all versions: format conversions + edit alternatives.

        Args:
            source_file: Path to source image file
            target_dir: Directory for format conversions (foto/video folder)
            edited_dir: Directory for edited versions (Upravené foto/video folder)

        Returns:
            List of dictionaries with info about generated files:
            [{'type': 'format', 'edit': None, 'path': '/path/to/file.png', 'original': '/source/file.jpg'},
             {'type': 'edit', 'edit': 'bw', 'path': '/path/to/file_bw.jpg', 'original': '/source/file.jpg'}, ...]
        """
        if not os.path.exists(source_file):
            logger.error(f"Source file does not exist: {source_file}")
            return []

        file_ext = os.path.splitext(source_file)[1].lower()
        if file_ext not in [ext.lower() for ext in IMAGE_EXTENSIONS]:
            logger.warning(f"Unsupported file type for alternatives: {file_ext}")
            return []

        generated_files = []

        # 1. Generate format conversions (PNG, TIF) - go to target_dir (only if formats enabled)
        format_files = []
        if self.enabled_formats:
            format_files = self._generate_format_conversions(source_file, target_dir)
            generated_files.extend(format_files)

        # 2. Generate edit alternatives for original format - go to edited_dir (only if effects enabled)
        if self.enabled_alternatives:
            original_alternatives = self._generate_edit_alternatives(source_file, edited_dir)
            generated_files.extend(original_alternatives)

            # 3. Generate edit alternatives for each converted format - go to edited_dir
            for format_file in format_files:
                format_alternatives = self._generate_edit_alternatives(format_file['path'], edited_dir)
                generated_files.extend(format_alternatives)

        logger.info(f"Generated {len(generated_files)} total alternative versions for {source_file}")
        return generated_files

    def _generate_format_conversions(self, source_file: str, target_dir: str) -> List[Dict[str, str]]:
        """Generate format conversions (PNG, TIF) of the original file."""
        generated_files = []

        for new_format in self.enabled_formats:
            try:
                # Get proper output path with correct directory structure
                output_path = get_format_conversion_path(source_file, new_format)

                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # Convert format
                success = self._convert_format(source_file, output_path, new_format)
                if success:
                    generated_files.append({
                        'type': 'format',
                        'edit': None,
                        'format': new_format,
                        'path': output_path,
                        'original': source_file,
                        'description': f'Format conversion to {new_format.upper()}'
                    })
                    logger.info(f"Generated format conversion: {output_path}")

            except Exception as e:
                logger.error(f"Failed to generate {new_format} conversion for {source_file}: {e}")

        return generated_files

    def _generate_edit_alternatives(self, source_file: str, edited_dir: str) -> List[Dict[str, str]]:
        """Generate edit alternatives (bw, negative, sharpen, misty, blurred) for a file."""
        generated_files = []

        for edit_tag in self.enabled_alternatives:
            if edit_tag not in ALTERNATIVE_EDIT_TAGS:
                logger.warning(f"Unknown edit tag: {edit_tag}")
                continue

            try:
                alt_file = self._generate_single_edit(source_file, edited_dir, edit_tag)
                if alt_file:
                    generated_files.append({
                        'type': 'edit',
                        'edit': edit_tag,
                        'format': os.path.splitext(alt_file)[1],
                        'path': alt_file,
                        'original': source_file,
                        'description': ALTERNATIVE_EDIT_TAGS[edit_tag]
                    })
                    logger.info(f"Generated {edit_tag} alternative: {alt_file}")

            except Exception as e:
                logger.error(f"Failed to generate {edit_tag} alternative for {source_file}: {e}")

        return generated_files

    def _convert_format(self, source_path: str, output_path: str, target_format: str) -> bool:
        """Convert file to different format with maximum quality."""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with Image.open(source_path) as img:
                # Convert to RGB if needed
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')

                if target_format.lower() == '.png':
                    # PNG with maximum quality
                    img.save(output_path, 'PNG', optimize=False, compress_level=0)
                elif target_format.lower() in ['.tif', '.tiff']:
                    # TIFF uncompressed with maximum quality
                    img.save(output_path, 'TIFF', compression=None, quality=100)
                else:
                    logger.error(f"Unsupported target format: {target_format}")
                    return False

                return True
        except Exception as e:
            logger.error(f"Failed to convert format from {source_path} to {output_path}: {e}")
            return False

    def _generate_single_edit(self, source_file: str, edited_dir: str, edit_tag: str) -> Optional[str]:
        """Generate single edit alternative."""
        # Create output filename with edit tag
        source_name = os.path.splitext(os.path.basename(source_file))[0]
        source_ext = os.path.splitext(source_file)[1]
        output_filename = f"{source_name}{edit_tag}{source_ext}"

        # Use get_format_conversion_path logic to get correct directory for the format
        temp_path = source_file.replace(os.path.basename(source_file), output_filename)
        output_path = get_format_conversion_path(temp_path, source_ext)

        # Replace "foto" with "Upravené foto" in the path
        output_path = output_path.replace("/foto/", "/Upravené foto/").replace("\\foto\\", "\\Upravené foto\\")
        output_path = output_path.replace("/Foto/", "/Upravené foto/").replace("\\Foto\\", "\\Upravené foto\\")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Apply the appropriate edit effect
        processor_method = getattr(self, f'_apply{edit_tag}', None)
        if not processor_method:
            logger.error(f"Processor method _apply{edit_tag} not found")
            return None

        success = processor_method(source_file, output_path)
        return output_path if success else None

    def _apply_bw(self, source_path: str, output_path: str) -> bool:
        """Convert image to black and white."""
        try:
            with Image.open(source_path) as img:
                # Convert to grayscale using luminance weights
                bw_img = img.convert('L')
                # Convert back to RGB to maintain format compatibility
                bw_rgb = Image.new('RGB', bw_img.size)
                bw_rgb.paste(bw_img)
                bw_rgb.save(output_path, quality=95, optimize=False)
                return True
        except Exception as e:
            logger.error(f"Failed to convert to B&W: {e}")
            return False

    def _apply_negative(self, source_path: str, output_path: str) -> bool:
        """Convert image to color negative."""
        try:
            with Image.open(source_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Invert colors (255 - pixel_value for each channel)
                negative_img = ImageOps.invert(img)
                negative_img.save(output_path, quality=95, optimize=False)
                return True
        except Exception as e:
            logger.error(f"Failed to convert to negative: {e}")
            return False

    def _apply_sharpen(self, source_path: str, output_path: str) -> bool:
        """Apply sharpening filter."""
        try:
            with Image.open(source_path) as img:
                # Apply unsharp mask for professional sharpening
                sharpened = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
                sharpened.save(output_path, quality=95, optimize=False)
                return True
        except Exception as e:
            logger.error(f"Failed to apply sharpening: {e}")
            return False

    def _apply_misty(self, source_path: str, output_path: str) -> bool:
        """Apply misty/foggy effect using Photoshop-like technique."""
        try:
            with Image.open(source_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Convert to numpy array for processing
                img_array = np.array(img).astype(np.float32)
                height, width = img_array.shape[:2]

                # Generate cloud-like noise pattern (similar to Photoshop's Clouds filter)
                np.random.seed(42)  # For reproducible results
                noise = np.random.rand(height, width) * 255

                # Apply Gaussian blur to create cloud texture
                noise_blurred = cv2.GaussianBlur(noise, (121, 121), 40)

                # Create fog overlay using Screen blend mode simulation
                # Screen formula: 1 - (1-base) * (1-overlay)
                fog_overlay = noise_blurred / 255.0

                # Apply screen blending to each channel with stronger fog intensity
                for channel in range(3):
                    base = img_array[:, :, channel] / 255.0
                    # Screen blend mode with stronger fog effect
                    result = 1.0 - (1.0 - base) * (1.0 - fog_overlay * 0.8)  # 0.8 for strong vapor/steam effect
                    img_array[:, :, channel] = result * 255.0

                # Ensure values are in valid range
                img_array = np.clip(img_array, 0, 255).astype(np.uint8)

                # Convert back to PIL Image and save
                misty_img = Image.fromarray(img_array)
                misty_img.save(output_path, quality=95, optimize=False)
                return True
        except Exception as e:
            logger.error(f"Failed to apply misty effect: {e}")
            return False

    def _apply_blurred(self, source_path: str, output_path: str) -> bool:
        """Apply Gaussian blur effect."""
        try:
            with Image.open(source_path) as img:
                # Apply Gaussian blur with radius similar to Photoshop (45px equivalent)
                blurred = img.filter(ImageFilter.GaussianBlur(radius=15))
                blurred.save(output_path, quality=95, optimize=False)
                return True
        except Exception as e:
            logger.error(f"Failed to apply blur: {e}")
            return False


def get_alternative_output_dirs(original_path: str) -> Tuple[str, str]:
    """
    Get output directories for format conversions and edited versions.

    Args:
        original_path: Original file path (e.g., "I:/Roztříděno/Foto/jpg/Abstrakty/2025/1/DSC0001.JPG")

    Returns:
        Tuple of (target_dir, edited_dir):
        - target_dir: For format conversions (stays in same location)
        - edited_dir: For edited versions (replaces "foto"/"video" with "Upravené foto"/"Upravené video")
    """
    path_obj = Path(original_path)
    path_parts = list(path_obj.parts)

    # Target dir is the same directory as original (for format conversions)
    target_dir = str(path_obj.parent)

    # Edited dir replaces "foto"/"video" part with "Upravené foto"/"Upravené video"
    edited_parts = path_parts[:-1]  # Remove filename
    for i, part in enumerate(edited_parts):
        part_lower = part.lower()
        if "foto" in part_lower and "upravené" not in part_lower:
            edited_parts[i] = part.replace("foto", "Upravené foto").replace("Foto", "Upravené foto")
            break
        elif "video" in part_lower and "upravené" not in part_lower:
            edited_parts[i] = part.replace("video", "Upravené video").replace("Video", "Upravené video")
            break

    edited_dir = str(Path(*edited_parts))

    return target_dir, edited_dir


def get_format_conversion_path(original_path: str, new_format: str) -> str:
    """
    Get path for format conversion, adjusting both filename and directory structure.

    Args:
        original_path: Original file path (e.g., "I:/Roztříděno/Foto/jpg/Abstrakty/DSC0001.JPG")
        new_format: New format extension (e.g., ".png", ".tif")

    Returns:
        Path for converted file (e.g., "I:/Roztříděno/Foto/png/Abstrakty/DSC0001.png")
    """
    path_obj = Path(original_path)
    path_parts = list(path_obj.parts)

    # Get original extension and new extension (without dots)
    original_ext = path_obj.suffix.lower().lstrip('.')
    new_ext = new_format.lower().lstrip('.')

    # Find and replace extension-based directory
    for i, part in enumerate(path_parts):
        if part.lower() == original_ext:
            path_parts[i] = new_ext
            break

    # Change filename extension
    filename_without_ext = path_obj.stem
    new_filename = f"{filename_without_ext}{new_format}"
    path_parts[-1] = new_filename

    return str(Path(*path_parts))