"""
Media display module for MediaViewer.

Handles image and video file display with responsive sizing.
"""

import os
import logging
import threading
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from typing import Optional
import cv2  # OpenCV for video capture

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

        # Video playback state (OpenCV)
        self.video_cap = None  # cv2.VideoCapture object
        self.video_thread = None  # Threading object for playback loop
        self.video_lock = threading.Lock()  # Thread lock for video_cap access
        self.video_fps = 0  # Frame rate
        self.video_frame_count = 0  # Total frames
        self.video_duration = 0  # Duration in seconds
        self.current_frame_number = 0  # Current playback position

        # User interaction flags
        self.user_seeking = False  # Flag to prevent progress bar updates during seek

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
            # Stop any existing video
            self.stop_video()

            # Store file path
            self.current_file_path = file_path

            # Show video controls
            if self.controls_frame:
                self.controls_frame.pack(fill=tk.X, padx=5, pady=5)

            # Open video with OpenCV
            with self.video_lock:
                self.video_cap = cv2.VideoCapture(file_path)

                if not self.video_cap.isOpened():
                    raise Exception("Failed to open video file")

                # Get video properties
                self.video_fps = self.video_cap.get(cv2.CAP_PROP_FPS)
                self.video_frame_count = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.video_duration = self.video_frame_count / self.video_fps if self.video_fps > 0 else 0
                self.current_frame_number = 0

                logging.debug(
                    f"Video loaded: {self.video_frame_count} frames, "
                    f"{self.video_fps:.2f} FPS, {self.video_duration:.2f}s duration"
                )

                # Display first frame
                self._display_frame()

            # Update time display
            self._update_time_display()

        except Exception as e:
            logging.error(f"Error loading video: {e}")
            if self.media_label:
                self.media_label.configure(image="", text=f"Error loading video:\n{str(e)}")

    def _display_frame(self):
        """Display current video frame in media_label."""
        if not self.video_cap or not self.media_label:
            return

        try:
            with self.video_lock:
                # Read current frame
                ret, frame = self.video_cap.read()

                if not ret:
                    logging.warning("Failed to read video frame")
                    return

                # Convert BGR (OpenCV) to RGB (PIL)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to PIL Image
                pil_image = Image.fromarray(frame_rgb)

                # Get display area size
                self.media_label.update_idletasks()
                display_width = max(self.media_label.winfo_width() - 20, 300)
                display_height = max(self.media_label.winfo_height() - 20, 200)

                # Calculate scaling to fit area while maintaining aspect ratio
                scale_x = display_width / pil_image.width
                scale_y = display_height / pil_image.height
                scale = min(scale_x, scale_y, 1.0)  # Never scale above 100%

                new_width = int(pil_image.width * scale)
                new_height = int(pil_image.height * scale)

                # Resize frame
                resized = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                self.current_image = ImageTk.PhotoImage(resized)

                # Display frame
                self.media_label.configure(image=self.current_image, text="")

        except Exception as e:
            logging.error(f"Error displaying video frame: {e}")

    def _update_time_display(self):
        """Update time label with current playback position."""
        if not self.time_label or not self.video_cap:
            return

        try:
            current_time = self.current_frame_number / self.video_fps if self.video_fps > 0 else 0
            total_time = self.video_duration

            # Format as MM:SS
            current_min = int(current_time // 60)
            current_sec = int(current_time % 60)
            total_min = int(total_time // 60)
            total_sec = int(total_time % 60)

            time_text = f"{current_min:02d}:{current_sec:02d} / {total_min:02d}:{total_sec:02d}"
            self.time_label.configure(text=time_text)

            # Update progress bar (only if user is not currently seeking)
            if self.video_progress and not self.user_seeking:
                progress_percent = (self.current_frame_number / self.video_frame_count * 100) if self.video_frame_count > 0 else 0
                self.video_progress.set(progress_percent)

        except Exception as e:
            logging.error(f"Error updating time display: {e}")

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
        if not self.current_file_path or not is_video_file(self.current_file_path) or not self.video_cap:
            return

        # Set playing state
        self.video_playing = True
        self.video_paused = False

        # Update button
        if self.play_button:
            self.play_button.configure(text="Pause")

        # Start playback thread if not already running
        if self.video_thread is None or not self.video_thread.is_alive():
            self.video_thread = threading.Thread(target=self._video_playback_loop, daemon=True)
            self.video_thread.start()
            logging.debug("Started video playback thread")

    def pause_video(self):
        """Pause video playback."""
        self.video_playing = False
        self.video_paused = True
        if self.play_button:
            self.play_button.configure(text="Play")
        logging.debug("Video paused")

    def stop_video(self):
        """Stop video playback and release resources."""
        # Stop playback
        self.video_playing = False
        self.video_paused = False

        # Wait for playback thread to finish
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=1.0)
            self.video_thread = None

        # Release video capture
        with self.video_lock:
            if self.video_cap:
                self.video_cap.release()
                self.video_cap = None

        # Reset video state
        self.video_fps = 0
        self.video_frame_count = 0
        self.video_duration = 0
        self.current_frame_number = 0

        # Update UI
        if self.play_button:
            self.play_button.configure(text="Play")
        if self.video_progress:
            self.video_progress.set(0)
        if self.time_label:
            self.time_label.configure(text="00:00 / 00:00")

        logging.debug("Video stopped and resources released")

    def seek_video(self, value):
        """
        Seek to position in video.

        Args:
            value: Position value (0-100)
        """
        if not self.current_file_path or not is_video_file(self.current_file_path) or not self.video_cap:
            return

        try:
            # Set flag to prevent playback loop from updating progress bar
            self.user_seeking = True

            # Calculate target frame
            target_frame = int((float(value) / 100.0) * self.video_frame_count)
            target_frame = max(0, min(target_frame, self.video_frame_count - 1))

            # Seek to target frame in separate thread to avoid blocking UI
            threading.Thread(target=self._seek_to_position, args=(target_frame,), daemon=True).start()

        except Exception as e:
            logging.error(f"Error seeking video: {e}")
            self.user_seeking = False

    def _seek_to_position(self, target_frame: int):
        """
        Seek to specific frame position (runs in separate thread).

        Args:
            target_frame: Target frame number
        """
        try:
            with self.video_lock:
                if not self.video_cap:
                    return

                # Set frame position
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                self.current_frame_number = target_frame

                # Display the seeked frame
                self._display_frame()

            # Update time display (thread-safe)
            self.root.after(0, self._update_time_display)

            logging.debug(f"Seeked to frame {target_frame}")

        except Exception as e:
            logging.error(f"Error in seek operation: {e}")

        finally:
            # Clear seeking flag after a short delay
            time.sleep(0.1)
            self.user_seeking = False

    def _video_playback_loop(self):
        """Background thread for video playback."""
        try:
            frame_delay = 1.0 / self.video_fps if self.video_fps > 0 else 0.033  # ~30 FPS fallback

            while self.video_playing and self.video_cap:
                loop_start = time.time()

                # Only advance frame if not seeking
                if not self.user_seeking:
                    with self.video_lock:
                        if not self.video_cap:
                            break

                        # Check if we've reached the end
                        if self.current_frame_number >= self.video_frame_count - 1:
                            # Loop back to start
                            self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            self.current_frame_number = 0
                            logging.debug("Video reached end, looping to start")

                        # Read and display next frame
                        ret, frame = self.video_cap.read()

                        if ret:
                            self.current_frame_number += 1

                            # Convert and display frame
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_image = Image.fromarray(frame_rgb)

                            # Get display area size
                            display_width = max(self.media_label.winfo_width() - 20, 300)
                            display_height = max(self.media_label.winfo_height() - 20, 200)

                            # Calculate scaling
                            scale_x = display_width / pil_image.width
                            scale_y = display_height / pil_image.height
                            scale = min(scale_x, scale_y, 1.0)

                            new_width = int(pil_image.width * scale)
                            new_height = int(pil_image.height * scale)

                            # Resize and convert to PhotoImage
                            resized = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            photo_image = ImageTk.PhotoImage(resized)

                            # Update display (thread-safe)
                            self.current_image = photo_image
                            self.root.after(0, lambda img=photo_image: self.media_label.configure(image=img, text=""))

                            # Update time display
                            self.root.after(0, self._update_time_display)

                # Calculate sleep time to maintain frame rate
                elapsed = time.time() - loop_start
                sleep_time = max(0, frame_delay - elapsed)
                time.sleep(sleep_time)

        except Exception as e:
            logging.error(f"Error in video playback loop: {e}")

        finally:
            logging.debug("Video playback loop exited")

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