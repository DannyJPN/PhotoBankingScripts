"""
Media display module for MediaViewer.

Handles image and video file display with responsive sizing.
"""

import os
import logging
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from typing import Optional

from givephotobankreadymediafileslib.media_helper import is_video_file


class MediaDisplay:
    """Manages media file display including images and videos."""

    def __init__(self, root: tk.Tk):
        """
        Initialize media display.

        Args:
            root: Tkinter root window
        """
        self.root = root

        # Current media state
        self.current_file_path: Optional[str] = None
        self.current_image: Optional[ImageTk.PhotoImage] = None
        self.original_image_size: Optional[tuple] = None
        self.video_surface = None
        self.video_playing = False
        self.video_paused = False

        # UI widget references (set by ui_components module)
        self.media_label: Optional[ttk.Label] = None
        self.controls_frame: Optional[ttk.Frame] = None
        self.play_button: Optional[ttk.Button] = None
        self.stop_button: Optional[ttk.Button] = None
        self.video_progress: Optional[ttk.Scale] = None
        self.time_label: Optional[ttk.Label] = None

    def load_image(self, file_path: str):
        """
        Load and display an image file with responsive sizing.

        Args:
            file_path: Path to image file
        """
        try:
            # Hide video controls
            if self.controls_frame:
                self.controls_frame.pack_forget()

            # Store file path
            self.current_file_path = file_path

            # Load original image to get size (use context manager to ensure file is closed)
            with Image.open(file_path) as image:
                self.original_image_size = image.size

            # Resize for current display area
            self.resize_image()

        except Exception as e:
            logging.error(f"Error loading image: {e}")
            if self.media_label:
                self.media_label.configure(image="", text=f"Error loading image:\n{str(e)}")

    def resize_image(self):
        """Resize current image to fit display area responsively."""
        if not self.current_file_path or not self.original_image_size or not self.media_label:
            return

        try:
            # Get current display area size
            self.media_label.update_idletasks()
            display_width = max(self.media_label.winfo_width() - 20, 300)
            display_height = max(self.media_label.winfo_height() - 20, 200)

            # Load image again (use context manager to ensure file is closed)
            with Image.open(self.current_file_path) as image:
                # Calculate scaling to fit area while maintaining aspect ratio
                # Never scale above 100% of original size
                scale_x = min(display_width / image.width, 1.0)
                scale_y = min(display_height / image.height, 1.0)
                scale = min(scale_x, scale_y)

                new_width = int(image.width * scale)
                new_height = int(image.height * scale)

                # Resize image
                resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                self.current_image = ImageTk.PhotoImage(resized)

            # Display image
            self.media_label.configure(image=self.current_image, text="")

        except Exception as e:
            logging.error(f"Error resizing image: {e}")

    def on_window_resize(self, event):
        """
        Handle window resize events.

        Args:
            event: Tkinter resize event
        """
        # Only resize image if it's the main window being resized
        if event.widget == self.root and self.current_file_path and not is_video_file(self.current_file_path):
            # Delay resize to avoid too many calls
            self.root.after(100, self.resize_image)

    def load_video(self, file_path: str):
        """
        Load and prepare video for playback.

        Args:
            file_path: Path to video file
        """
        try:
            # Store file path
            self.current_file_path = file_path

            # Show video controls
            if self.controls_frame:
                self.controls_frame.pack(fill=tk.X, padx=5, pady=5)

            # For now, show video info and thumbnail
            if self.media_label:
                self.media_label.configure(
                    image="",
                    text=f"Video file:\n{os.path.basename(file_path)}\n\nUse controls below to play"
                )

        except Exception as e:
            logging.error(f"Error loading video: {e}")
            if self.media_label:
                self.media_label.configure(image="", text=f"Error loading video:\n{str(e)}")

    def clear_media(self):
        """Clear current media display."""
        self.current_image = None
        self.current_file_path = None
        self.original_image_size = None
        if self.media_label:
            self.media_label.configure(image="", text="No media loaded")
        self.stop_video()

    def toggle_video(self):
        """Toggle video play/pause."""
        if self.video_playing:
            self.pause_video()
        else:
            self.play_video()

    def play_video(self):
        """Start video playback."""
        if self.current_file_path and is_video_file(self.current_file_path):
            self.video_playing = True
            self.video_paused = False
            if self.play_button:
                self.play_button.configure(text="Pause")

    def pause_video(self):
        """Pause video playback."""
        self.video_playing = False
        self.video_paused = True
        if self.play_button:
            self.play_button.configure(text="Play")

    def stop_video(self):
        """Stop video playback."""
        self.video_playing = False
        self.video_paused = False
        if self.play_button:
            self.play_button.configure(text="Play")
        if self.video_progress:
            self.video_progress.set(0)

    def seek_video(self, value):
        """
        Seek to position in video.

        Args:
            value: Position value (0-100)
        """
        if self.current_file_path and is_video_file(self.current_file_path):
            logging.debug(f"Seeking to {float(value):.1f}%")

    def load_media(self, file_path: str):
        """
        Load media file (image or video).

        Args:
            file_path: Path to media file
        """
        if is_video_file(file_path):
            self.load_video(file_path)
        else:
            self.load_image(file_path)