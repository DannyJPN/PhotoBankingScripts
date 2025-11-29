"""
Media display logic for images and videos.

This module handles:
- Image loading, resizing, and responsive display
- Video playback preparation and control
- Media file type detection and display clearing
"""

import os
import logging
from typing import Optional, Tuple
from PIL import Image, ImageTk
import pygame
import tkinter as tk
from tkinter import ttk

from givephotobankreadymediafileslib.media_helper import is_video_file


def initialize_pygame() -> None:
    """
    Initialize pygame for video playback.

    :raises: Exception if pygame initialization fails
    """
    pygame.init()
    pygame.mixer.init()


def load_image_file(file_path: str) -> Tuple[Image.Image, Tuple[int, int]]:
    """
    Load an image file and return the PIL Image and its original size.

    :param file_path: Path to the image file
    :return: Tuple of (PIL Image, (width, height))
    :raises: Exception if image loading fails
    """
    try:
        image = Image.open(file_path)
        original_size = image.size
        return image, original_size
    except Exception as e:
        logging.error(f"Error loading image from {file_path}: {e}")
        raise


def resize_image_to_fit(
    image: Image.Image,
    display_width: int,
    display_height: int,
    max_scale: float = 1.0
) -> Image.Image:
    """
    Resize image to fit display area while maintaining aspect ratio.

    :param image: PIL Image to resize
    :param display_width: Available display width in pixels
    :param display_height: Available display height in pixels
    :param max_scale: Maximum scaling factor (1.0 = never scale above original size)
    :return: Resized PIL Image
    """
    # Calculate scaling to fit area while maintaining aspect ratio
    scale_x = min(display_width / image.width, max_scale)
    scale_y = min(display_height / image.height, max_scale)
    scale = min(scale_x, scale_y)

    new_width = int(image.width * scale)
    new_height = int(image.height * scale)

    # Resize image
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return resized_image


def create_photo_image(image: Image.Image) -> ImageTk.PhotoImage:
    """
    Convert PIL Image to Tkinter PhotoImage.

    :param image: PIL Image to convert
    :return: Tkinter PhotoImage
    """
    return ImageTk.PhotoImage(image)


def display_image_in_label(
    label: ttk.Label,
    file_path: str,
    display_width: int,
    display_height: int
) -> Optional[ImageTk.PhotoImage]:
    """
    Load, resize, and display an image in a Tkinter label.

    :param label: Tkinter label widget to display image in
    :param file_path: Path to the image file
    :param display_width: Available display width in pixels
    :param display_height: Available display height in pixels
    :return: PhotoImage object (must be stored to prevent garbage collection) or None on error
    """
    try:
        # Load image
        image, _ = load_image_file(file_path)

        # Resize to fit display
        resized_image = resize_image_to_fit(image, display_width, display_height)

        # Convert to PhotoImage
        photo_image = create_photo_image(resized_image)

        # Display in label
        label.configure(image=photo_image, text="")

        return photo_image

    except Exception as e:
        logging.error(f"Error displaying image: {e}")
        label.configure(image="", text=f"Error loading image:\n{str(e)}")
        return None


def display_video_placeholder(label: ttk.Label, file_path: str) -> None:
    """
    Display a placeholder for video files.

    :param label: Tkinter label widget to display placeholder in
    :param file_path: Path to the video file
    """
    try:
        filename = os.path.basename(file_path)
        label.configure(
            image="",
            text=f"Video file:\n{filename}\n\nUse controls below to play"
        )
    except Exception as e:
        logging.error(f"Error displaying video placeholder: {e}")
        label.configure(image="", text=f"Error loading video:\n{str(e)}")


def clear_media_display(label: ttk.Label) -> None:
    """
    Clear media display label.

    :param label: Tkinter label widget to clear
    """
    label.configure(image="", text="No media loaded")


def get_display_dimensions(label: ttk.Label, min_width: int = 300, min_height: int = 200) -> Tuple[int, int]:
    """
    Get current display dimensions of a label widget.

    :param label: Tkinter label widget
    :param min_width: Minimum width to return
    :param min_height: Minimum height to return
    :return: Tuple of (width, height) in pixels
    """
    label.update_idletasks()
    width = max(label.winfo_width() - 20, min_width)
    height = max(label.winfo_height() - 20, min_height)
    return width, height