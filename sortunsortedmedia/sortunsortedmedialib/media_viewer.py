"""
Graphical media viewer with responsive layout for categorizing files.
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
from typing import Optional, Callable, List
import threading
import time
import cv2
import subprocess

# Try to import rawpy for RAW format support
try:
    import rawpy
    RAWPY_AVAILABLE = True
except ImportError:
    RAWPY_AVAILABLE = False
    logging.warning("rawpy not installed - RAW files will show small thumbnails only")

from sortunsortedmedialib.constants import CAMERA_REGEXES, RAW_EXTENSIONS
from sortunsortedmedialib.media_helper import is_video_file, is_jpg_file
from sortunsortedmedialib.media_classifier import detect_camera_from_filename
from sortunsortedmedialib.exif_camera_detector import combine_regex_and_exif_detection


class MediaViewer:
    def __init__(self, root: tk.Tk, target_folder: str):
        self.root = root
        self.root.title("Media Viewer & Categorizer")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # Current media info
        self.target_folder = target_folder
        self.current_file_path: Optional[str] = None
        self.current_image: Optional[ImageTk.PhotoImage] = None
        self.original_image_size: Optional[tuple] = None
        self.cached_pil_image: Optional[Image.Image] = None  # Cache for preloaded/RAW images

        # Video playback attributes
        self.video_playing = False
        self.video_paused = False
        self.video_cap = None  # cv2.VideoCapture object
        self.video_thread = None  # Threading object for playback loop
        self.video_lock = threading.Lock()  # Thread lock for video_cap access
        self.video_fps = 0  # Frame rate
        self.video_frame_count = 0  # Total frames
        self.video_duration = 0  # Duration in seconds
        self.current_frame_number = 0  # Current position

        self.completion_callback: Optional[Callable] = None

        # Keyboard shortcut state for cycling through categories
        self.categories_by_letter: dict[str, List[str]] = {}
        self.last_pressed_letter: Optional[str] = None
        self.current_cycle_index: int = 0
        
        self.setup_ui()

        # Bind resize event for responsive image display
        self.root.bind('<Configure>', self.on_window_resize)

        # Bind keyboard shortcuts for category selection (A-Z)
        self.root.bind('<Key>', self.handle_keyboard_shortcut)

        # Bind Enter key globally for processing file
        self.root.bind('<Return>', self.handle_enter_key)

        # Bind mouse click globally to remove focus from entry widgets
        self.root.bind_all('<Button-1>', self.on_global_click, '+')

        # Handle window close event (equivalent to Ctrl+C)
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
    def setup_ui(self):
        """Setup the main UI layout."""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for media display
        self.setup_media_panel(main_paned)
        
        # Right panel for terminal-like interface
        self.setup_terminal_panel(main_paned)
        
    def setup_media_panel(self, parent):
        """Setup the left panel for media display."""
        media_frame = ttk.Frame(parent)
        parent.add(media_frame, weight=2)

        # Bind click to remove focus from entry widgets
        media_frame.bind('<Button-1>', self.remove_entry_focus)

        # Media display area
        self.media_label = ttk.Label(media_frame, text="No media loaded",
                                   anchor=tk.CENTER, background='black', foreground='white')
        self.media_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.media_label.bind('<Button-1>', self.remove_entry_focus)
        
        # Video controls frame
        controls_frame = ttk.Frame(media_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.play_button = ttk.Button(controls_frame, text="Play", command=self.toggle_video)
        self.play_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(controls_frame, text="Stop", command=self.stop_video)
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # Video progress bar
        self.video_progress = ttk.Scale(controls_frame, orient=tk.HORIZONTAL,
                                      from_=0, to=100)
        self.video_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Bind manual seeking to mouse button release (not command callback to avoid oscillation)
        self.video_progress.bind('<ButtonRelease-1>', self.on_seek_manual)
        
        # Time labels
        self.time_label = ttk.Label(controls_frame, text="00:00 / 00:00")
        self.time_label.pack(side=tk.RIGHT, padx=2)
        
        # Initially hide video controls
        controls_frame.pack_forget()
        self.controls_frame = controls_frame
        
    def setup_terminal_panel(self, parent):
        """Setup the right panel with categorization interface."""
        control_frame = ttk.Frame(parent)
        parent.add(control_frame, weight=1)
        
        # File path display
        path_frame = ttk.LabelFrame(control_frame, text="Current File")
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.file_path_label = ttk.Label(path_frame, text="No file loaded", 
                                       wraplength=300, justify=tk.LEFT)
        self.file_path_label.pack(padx=10, pady=10, anchor=tk.W)
        
        # Camera detection and editing
        camera_frame = ttk.LabelFrame(control_frame, text="Camera")
        camera_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(camera_frame, text="Detected:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        self.camera_label = ttk.Label(camera_frame, text="Unknown", foreground="blue")
        self.camera_label.pack(anchor=tk.W, padx=10, pady=(0, 5))
        
        ttk.Label(camera_frame, text="Edit camera name:").pack(anchor=tk.W, padx=10, pady=(5, 5))
        self.camera_entry = ttk.Entry(camera_frame, font=('Arial', 10))
        self.camera_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Manual input frame
        input_frame = ttk.LabelFrame(control_frame, text="Category Selection")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Enter category:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.input_entry = ttk.Entry(input_frame, font=('Arial', 12))
        self.input_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.input_entry.bind('<Return>', self.handle_input)

        # Action buttons frame
        action_buttons_frame = ttk.Frame(input_frame)
        action_buttons_frame.pack(pady=(0, 10))

        # Process button
        self.process_button = ttk.Button(action_buttons_frame, text="Process File",
                                       command=self.process_current_file)
        self.process_button.pack(side=tk.LEFT, padx=2)

        # Open in Explorer button
        self.explorer_button = ttk.Button(action_buttons_frame, text="Open in Explorer",
                                        command=self.open_in_explorer)
        self.explorer_button.pack(side=tk.LEFT, padx=2)
        
        # Category suggestions from target folder
        self.setup_category_buttons(control_frame)
        
    def get_categories_from_target_folder(self) -> List[str]:
        """Extract categories from target folder at depth 3: target_folder/*/*/CATEGORY/"""
        categories = set()
        
        try:
            # Categories are at depth 3: target_folder/level1/level2/CATEGORY/
            for level1 in os.listdir(self.target_folder):
                level1_path = os.path.join(self.target_folder, level1)
                if os.path.isdir(level1_path):
                    try:
                        for level2 in os.listdir(level1_path):
                            level2_path = os.path.join(level1_path, level2)
                            if os.path.isdir(level2_path):
                                try:
                                    for category in os.listdir(level2_path):
                                        category_path = os.path.join(level2_path, category)
                                        if os.path.isdir(category_path):
                                            categories.add(category)
                                except (PermissionError, OSError):
                                    continue
                    except (PermissionError, OSError):
                        continue
                        
        except (PermissionError, OSError) as e:
            logging.warning(f"Could not read categories from target folder: {e}")
        
        return sorted(list(categories))
    
    def setup_category_buttons(self, parent):
        """Setup quick category selection buttons from target folder with flow layout."""
        button_frame = ttk.LabelFrame(parent, text="Quick Categories")
        button_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create scrollable frame for categories
        canvas = tk.Canvas(button_frame)
        scrollbar = ttk.Scrollbar(button_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_reqwidth())

        # Get categories from target folder
        categories = self.get_categories_from_target_folder()

        if not categories:
            # Fallback to some categories if none found
            categories = ["Astro", "Flora", "Krajiny", "Ostatní", "Rostliny", "Zvěř"]

        # Store categories as class attribute for keyboard shortcuts
        self.categories = categories

        # Build index of categories by first letter for keyboard shortcuts
        self.categories_by_letter = {}
        for category in categories:
            if category:  # Skip empty strings
                first_letter = category[0].upper()
                if first_letter not in self.categories_by_letter:
                    self.categories_by_letter[first_letter] = []
                self.categories_by_letter[first_letter].append(category)

        # Store references for dynamic layout
        self.categories_canvas = canvas
        self.categories_scrollable_frame = scrollable_frame
        self.categories_list = categories

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Delay layout calculation until window is fully rendered
        self.root.after(100, self._layout_category_buttons)

        # Bind canvas resize to re-layout buttons
        canvas.bind("<Configure>", lambda e: self._layout_category_buttons())
            
    def load_media(self, file_path: str, completion_callback: Optional[Callable] = None, preloaded_image: Optional[Image.Image] = None):
        """Load and display media file.

        Args:
            file_path: Path to the media file
            completion_callback: Callback function when processing is complete
            preloaded_image: Pre-loaded PIL Image (for RAW files to avoid GUI blocking)
        """
        self.current_file_path = file_path
        self.completion_callback = completion_callback

        # Clear previous media
        self.clear_media()

        # Update file path display
        self.file_path_label.configure(text=file_path)

        # Update camera detection
        detected_camera = self.detect_camera()
        self.camera_label.configure(text=detected_camera)

        if is_video_file(file_path):
            self.load_video(file_path)
        else:
            self.load_image(file_path, preloaded_image=preloaded_image)

        # Set focus to main window (not textbox) so keyboard shortcuts work immediately
        self.root.focus_set()
        
    def is_raw_file(self, file_path: str) -> bool:
        """Check if file is a RAW format using constants."""
        return os.path.splitext(file_path)[1].lower() in RAW_EXTENSIONS

    def load_image(self, file_path: str, preloaded_image: Optional[Image.Image] = None):
        """Load and display an image file with responsive sizing.

        Args:
            file_path: Path to the image file
            preloaded_image: Pre-loaded PIL Image (avoids reloading RAW files)
        """
        try:
            # Hide video controls
            self.controls_frame.pack_forget()

            # Use preloaded image if provided (for RAW files - NO GUI BLOCKING!)
            if preloaded_image is not None:
                logging.info(f"Using preloaded image: {preloaded_image.size}")
                image = preloaded_image
            # Otherwise load from file
            elif self.is_raw_file(file_path) and RAWPY_AVAILABLE:
                # Load RAW file with rawpy for full resolution
                logging.info(f"Loading RAW file with rawpy: {file_path}")
                try:
                    with rawpy.imread(file_path) as raw:
                        rgb = raw.postprocess(
                            use_camera_wb=True,
                            use_auto_wb=False,
                            output_bps=8,
                            no_auto_bright=True,
                            output_color=rawpy.ColorSpace.sRGB
                        )
                        image = Image.fromarray(rgb)
                        logging.info(f"RAW file loaded successfully: {image.size}")
                except Exception as raw_error:
                    logging.warning(f"Failed to load RAW with rawpy: {raw_error}, falling back to embedded preview")
                    image = Image.open(file_path)  # Fallback to thumbnail
            else:
                # Load standard image file
                if self.is_raw_file(file_path) and not RAWPY_AVAILABLE:
                    logging.warning(f"RAW file detected but rawpy not available - loading thumbnail only")
                image = Image.open(file_path)

            # Cache the loaded image for faster resize operations
            self.cached_pil_image = image
            self.original_image_size = image.size

            # Resize for current display area
            self.resize_image()

        except Exception as e:
            logging.error(f"Error loading image: {e}")
            self.media_label.configure(image="", text=f"Error loading image:\n{str(e)}")
            
    def resize_image(self):
        """Resize current image to fit display area responsively."""
        if not self.current_file_path or not self.original_image_size:
            return

        try:
            # Get current display area size
            self.media_label.update_idletasks()
            display_width = max(self.media_label.winfo_width() - 20, 300)
            display_height = max(self.media_label.winfo_height() - 20, 200)

            # Use cached image if available (MUCH faster, especially for RAW files!)
            if self.cached_pil_image is not None:
                image = self.cached_pil_image
            else:
                # Fallback to loading from file (shouldn't happen with preloading)
                image = Image.open(self.current_file_path)

            # Calculate scaling to fit area while maintaining aspect ratio
            # Never scale above 100% of original size
            scale_x = min(display_width / image.width, 1.0)
            scale_y = min(display_height / image.height, 1.0)
            scale = min(scale_x, scale_y)

            new_width = int(image.width * scale)
            new_height = int(image.height * scale)

            # Resize image (work on copy to preserve cache)
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            self.current_image = ImageTk.PhotoImage(resized_image)

            # Display image
            self.media_label.configure(image=self.current_image, text="")

        except Exception as e:
            logging.error(f"Error resizing image: {e}")
            
    def on_window_resize(self, event):
        """Handle window resize events."""
        # Only resize image if it's the main window being resized
        if event.widget == self.root and self.current_file_path and not is_video_file(self.current_file_path):
            # Delay resize to avoid too many calls
            self.root.after(100, self.resize_image)
            
    def load_video(self, file_path: str):
        """Load and prepare video for playback, displaying first frame at full size."""
        try:
            # Show video controls
            self.controls_frame.pack(fill=tk.X, padx=5, pady=5)

            # Release previous video if any
            if self.video_cap is not None:
                self.video_cap.release()

            # Open video with OpenCV
            self.video_cap = cv2.VideoCapture(file_path)

            if not self.video_cap.isOpened():
                raise Exception("Failed to open video file")

            # Get video metadata
            self.video_fps = self.video_cap.get(cv2.CAP_PROP_FPS)
            self.video_frame_count = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.video_duration = self.video_frame_count / self.video_fps if self.video_fps > 0 else 0
            self.current_frame_number = 0

            logging.info(f"Video loaded: {self.video_fps:.2f} FPS, {self.video_frame_count} frames, {self.video_duration:.2f}s duration")

            # Force window to render and complete layout so we get correct sizes
            self.root.update()

            # Read and display first frame AT FULL SIZE
            ret, frame = self.video_cap.read()
            if ret:
                self._display_frame(frame)
                # Update time display
                self._update_time_display(0, self.video_duration)
                # Reset progress bar
                self.video_progress.set(0)
            else:
                raise Exception("Failed to read first frame")

        except Exception as e:
            logging.error(f"Error loading video: {e}")
            self.media_label.configure(image="", text=f"Error loading video:\n{str(e)}")
            if self.video_cap is not None:
                self.video_cap.release()
                self.video_cap = None
            
    def clear_media(self):
        """Clear current media display and release video resources."""
        self.current_image = None
        self.cached_pil_image = None  # Clear cache
        self.media_label.configure(image="", text="No media loaded")
        self.stop_video()

        # Release video capture if exists
        if self.video_cap is not None:
            self.video_cap.release()
            self.video_cap = None

        # Hide video controls
        self.controls_frame.pack_forget()

    def toggle_video(self):
        """Toggle video play/pause."""
        if self.video_playing:
            self.pause_video()
        else:
            self.play_video()

    def play_video(self):
        """Start video playback with threading."""
        if not self.current_file_path or not is_video_file(self.current_file_path):
            return

        if self.video_cap is None:
            logging.warning("No video loaded")
            return

        # Set playing state
        self.video_playing = True
        self.video_paused = False
        self.play_button.configure(text="Pause")

        # Start video playback thread
        if self.video_thread is None or not self.video_thread.is_alive():
            self.video_thread = threading.Thread(target=self._video_playback_loop, daemon=True)
            self.video_thread.start()
            logging.info("Video playback thread started")

    def pause_video(self):
        """Pause video playback."""
        self.video_playing = False
        self.video_paused = True
        self.play_button.configure(text="Play")

    def stop_video(self):
        """Stop video playback and reset to first frame."""
        # Stop playback
        self.video_playing = False
        self.video_paused = False
        self.play_button.configure(text="Play")

        # Wait for thread to finish
        if self.video_thread is not None and self.video_thread.is_alive():
            self.video_thread.join(timeout=1.0)

        # Reset to first frame (thread-safe with lock)
        if self.video_cap is not None:
            with self.video_lock:
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_frame_number = 0

                # Display first frame
                ret, frame = self.video_cap.read()

            if ret:
                self._display_frame(frame)
                self._update_time_display(0, self.video_duration)

        # Reset progress bar
        self.video_progress.set(0)

    def on_seek_manual(self, event):
        """
        Handle manual seeking when user releases mouse button on progress bar.

        This is called only for user-initiated seeks, NOT for programmatic updates.

        Args:
            event: Tkinter event object
        """
        # Get current progress bar value
        value = self.video_progress.get()
        self._seek_to_position(value)

    def _seek_to_position(self, value):
        """
        Internal method to seek to position in video (rounded to 1 second granularity).

        Args:
            value: Progress bar value (0-100)
        """
        if not self.current_file_path or not is_video_file(self.current_file_path):
            return

        if self.video_cap is None:
            return

        try:
            # Calculate target time (rounded to 1 second)
            target_percent = float(value)
            target_seconds = (target_percent / 100.0) * self.video_duration
            target_seconds = round(target_seconds)  # Round to 1 second granularity

            # Calculate target frame number
            target_frame = int(target_seconds * self.video_fps)
            target_frame = max(0, min(target_frame, self.video_frame_count - 1))

            # Seek video to target frame (thread-safe with lock)
            with self.video_lock:
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                self.current_frame_number = target_frame

                # Read and display frame at new position
                ret, frame = self.video_cap.read()

            if ret:
                self._display_frame(frame)
                current_time = target_frame / self.video_fps if self.video_fps > 0 else 0
                self._update_time_display(current_time, self.video_duration)

        except Exception as e:
            logging.error(f"Error seeking video: {e}")
        
    def detect_camera(self) -> str:
        """Detect camera using combined regex and EXIF detection."""
        if not self.current_file_path:
            return "Unknown"
            
        filename = os.path.basename(self.current_file_path)
        name, _ = os.path.splitext(filename)
        
        # Use regex detection first
        regex_camera = detect_camera_from_filename(name)
        
        # Combine with EXIF detection
        combined_camera = combine_regex_and_exif_detection(self.current_file_path, regex_camera)
        
        # Pre-fill the camera entry field with detected camera
        self.camera_entry.delete(0, tk.END)
        self.camera_entry.insert(0, combined_camera)
        
        return combined_camera
        
    def _layout_category_buttons(self):
        """Dynamically layout category buttons based on canvas width."""
        if not hasattr(self, 'categories_canvas') or not hasattr(self, 'categories_list'):
            return

        # Clear existing buttons
        for widget in self.categories_scrollable_frame.winfo_children():
            widget.destroy()

        # Get actual canvas width
        self.categories_canvas.update_idletasks()
        canvas_width = self.categories_canvas.winfo_width()

        if canvas_width <= 1:  # Canvas not yet rendered
            return

        # Calculate number of columns that will fit
        button_min_width = 100  # Minimum button width in pixels
        padding = 10  # Padding per button (padx * 2 + some margin)
        effective_button_width = button_min_width + padding

        max_cols = max(1, (canvas_width - 20) // effective_button_width)  # Subtract scrollbar width

        logging.debug(f"Canvas width: {canvas_width}, calculated max_cols: {max_cols}")

        # Place buttons in grid
        for i, category in enumerate(self.categories_list):
            row = i // max_cols
            col = i % max_cols
            btn = ttk.Button(self.categories_scrollable_frame, text=category,
                           command=lambda c=category: self.select_category(c))
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')

        # Configure column weights
        for col in range(max_cols):
            self.categories_scrollable_frame.columnconfigure(col, weight=1)

        # Update canvas window width to match canvas
        self.categories_canvas.itemconfig(
            self.categories_canvas.find_withtag("all")[0],
            width=canvas_width - 20  # Account for scrollbar
        )

    def select_category(self, category: str):
        """Select category from quick buttons."""
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, category)
        
    def handle_input(self, event):
        """Handle user input from entry field."""
        self.process_current_file()
        
    def process_current_file(self):
        """Process the current file with selected category."""
        category = self.input_entry.get().strip()
        if not category:
            messagebox.showwarning("No Category", "Please enter a category or select one from the buttons.")
            return

        # Get camera from user input (editable field)
        final_camera = self.camera_entry.get().strip() or "Unknown"

        # Close window and call completion callback
        if self.completion_callback:
            self.completion_callback(category, final_camera)

        self.root.destroy()

    def open_in_explorer(self):
        """Open the current file location in Windows Explorer."""
        if not self.current_file_path:
            messagebox.showwarning("No File", "No file is currently loaded.")
            return

        try:
            import subprocess
            import platform

            if platform.system() == "Windows":
                # Normalize path to use backslashes for Windows Explorer
                normalized_path = os.path.normpath(self.current_file_path)
                # Use Windows Explorer to show file and select it
                # Don't use check=True as Explorer sometimes returns non-zero exit codes even on success
                result = subprocess.run(['explorer', '/select,', normalized_path])
                logging.debug(f"Opened file location in Explorer: {normalized_path} (exit code: {result.returncode})")
            else:
                # For other systems, just open the directory
                directory = os.path.dirname(self.current_file_path)
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(['open', directory])
                else:  # Linux and others
                    subprocess.run(['xdg-open', directory])
                logging.debug(f"Opened directory: {directory}")

        except Exception as e:
            logging.error(f"Failed to open file location: {e}")
            messagebox.showerror("Error", f"Failed to open file location:\n{str(e)}")

    def remove_entry_focus(self, event):
        """
        Remove focus from entry widgets when clicking on other areas.

        This allows keyboard shortcuts to work after clicking outside textboxes.
        """
        self.root.focus_set()

    def on_global_click(self, event):
        """
        Handle global mouse clicks to remove focus from Entry widgets.

        If user clicks anywhere except on an Entry widget, remove focus.
        """
        # Check if the clicked widget is an Entry
        clicked_widget = event.widget
        if not isinstance(clicked_widget, (ttk.Entry, tk.Entry)):
            # Clicked outside Entry - remove focus
            self.root.focus_set()

    def handle_enter_key(self, event):
        """
        Handle Enter key press globally to process the file.

        Only processes if a category is entered.
        """
        # Process the file (will check if category is filled)
        self.process_current_file()

    def handle_keyboard_shortcut(self, event):
        """
        Handle keyboard shortcuts for category selection by first letter.

        Shortcuts only work when focus is NOT in an Entry widget.
        Press a letter (A-Z) to select category starting with that letter.
        Repeated presses cycle through categories with the same first letter.
        """
        # Ignore keyboard shortcuts if focus is in an Entry widget
        if isinstance(event.widget, (ttk.Entry, tk.Entry)):
            return

        # Check if the pressed key is a letter A-Z
        if event.char and event.char.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            pressed_letter = event.char.upper()

            # Check if we have categories starting with this letter
            if pressed_letter in self.categories_by_letter:
                categories_for_letter = self.categories_by_letter[pressed_letter]

                # If same letter pressed again, cycle to next category
                if pressed_letter == self.last_pressed_letter:
                    self.current_cycle_index = (self.current_cycle_index + 1) % len(categories_for_letter)
                else:
                    # Different letter pressed, start from first category
                    self.last_pressed_letter = pressed_letter
                    self.current_cycle_index = 0

                # Select the category
                category = categories_for_letter[self.current_cycle_index]
                self.select_category(category)
                logging.debug(f"Keyboard shortcut: {pressed_letter} -> {category} (index {self.current_cycle_index + 1}/{len(categories_for_letter)})")

    def on_window_close(self):
        """Handle window close event - equivalent to Ctrl+C."""
        logging.info("Window closed by user - terminating script")
        self.root.destroy()

        # Exit the entire script (equivalent to Ctrl+C)
        import sys
        sys.exit(0)

    def _display_frame(self, frame):
        """
        Display a video frame in the media label, resized to fit display area.

        Args:
            frame: OpenCV frame (BGR format) from cv2.VideoCapture
        """
        try:
            # Get current display area size
            self.media_label.update_idletasks()
            display_width = max(self.media_label.winfo_width() - 20, 300)
            display_height = max(self.media_label.winfo_height() - 20, 200)

            # Convert BGR to RGB (OpenCV uses BGR, PIL uses RGB)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Get frame dimensions
            frame_height, frame_width = frame.shape[:2]

            # Calculate scaling to fit area while maintaining aspect ratio
            scale_x = display_width / frame_width
            scale_y = display_height / frame_height
            scale = min(scale_x, scale_y, 1.0)  # Never scale above 100%

            new_width = int(frame_width * scale)
            new_height = int(frame_height * scale)

            # Resize frame
            resized_frame = cv2.resize(frame_rgb, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

            # Convert to PIL Image then to PhotoImage
            pil_image = Image.fromarray(resized_frame)
            self.current_image = ImageTk.PhotoImage(pil_image)

            # Display frame
            self.media_label.configure(image=self.current_image, text="")

        except Exception as e:
            logging.error(f"Error displaying frame: {e}")

    def _update_time_display(self, current_seconds: float, total_seconds: float):
        """
        Update the time label showing current/total time.

        Args:
            current_seconds: Current position in seconds
            total_seconds: Total duration in seconds
        """
        current_str = self._format_time(current_seconds)
        total_str = self._format_time(total_seconds)
        self.time_label.configure(text=f"{current_str} / {total_str}")

    def _format_time(self, seconds: float) -> str:
        """
        Format seconds as MM:SS.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted string MM:SS
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def _video_playback_loop(self):
        """
        Background thread loop for video playback.

        Reads frames from video, synchronizes with FPS, and displays them.
        Handles play/pause state and updates progress bar.
        """
        logging.info("Video playback thread started")

        try:
            while self.video_playing:
                # Check if paused
                if self.video_paused:
                    time.sleep(0.1)
                    continue

                # Read next frame (thread-safe with lock)
                with self.video_lock:
                    ret, frame = self.video_cap.read()

                if not ret:
                    # End of video - stop and stay on last frame
                    logging.info("Reached end of video")
                    self.root.after(0, self.stop_video)
                    break

                # Update frame number
                self.current_frame_number += 1
                current_time = self.current_frame_number / self.video_fps if self.video_fps > 0 else 0

                # Display frame in GUI thread (copy frame to prevent numpy array mutation)
                self.root.after(0, lambda f=frame.copy(): self._display_frame(f))

                # Update progress bar and time display in GUI thread
                progress_percent = (self.current_frame_number / self.video_frame_count * 100) if self.video_frame_count > 0 else 0
                self.root.after(0, lambda p=progress_percent: self.video_progress.set(p))
                self.root.after(0, lambda t=current_time: self._update_time_display(t, self.video_duration))

                # Synchronize with FPS (sleep for frame duration)
                if self.video_fps > 0:
                    frame_duration = 1.0 / self.video_fps
                    time.sleep(frame_duration)

        except Exception as e:
            logging.error(f"Error in video playback loop: {e}")
        finally:
            logging.info("Video playback thread stopped")


def show_media_viewer(file_path: str, target_folder: str, completion_callback: Optional[Callable] = None, preloaded_image: Optional[Image.Image] = None):
    """Show the media viewer for a specific file.

    Args:
        file_path: Path to the media file
        target_folder: Target folder for sorted media
        completion_callback: Callback function when processing is complete
        preloaded_image: Pre-loaded PIL Image (for RAW files to avoid GUI blocking)
    """
    root = tk.Tk()
    viewer = MediaViewer(root, target_folder)
    viewer.load_media(file_path, completion_callback, preloaded_image=preloaded_image)

    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()
    

if __name__ == "__main__":
    # Test the viewer
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        show_media_viewer(test_file)
    else:
        print("Usage: python media_viewer.py <media_file>")