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
import pygame
from typing import Optional, Callable, List
import threading
import time

from sortunsortedmedialib.constants import CAMERA_REGEXES
from sortunsortedmedialib.media_helper import is_video_file, is_jpg_file
from sortunsortedmedialib.media_classifier import detect_camera_from_filename
from sortunsortedmedialib.exif_camera_detector import combine_regex_and_exif_detection


class MediaViewer:
    def __init__(self, root: tk.Tk, target_folder: str):
        self.root = root
        self.root.title("Media Viewer & Categorizer")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize pygame for video playback
        pygame.init()
        pygame.mixer.init()
        
        # Current media info
        self.target_folder = target_folder
        self.current_file_path: Optional[str] = None
        self.current_image: Optional[ImageTk.PhotoImage] = None
        self.original_image_size: Optional[tuple] = None
        self.video_surface = None
        self.video_playing = False
        self.video_paused = False
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
                                      from_=0, to=100, command=self.seek_video)
        self.video_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
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
        
        # Process button
        self.process_button = ttk.Button(input_frame, text="Process File", 
                                       command=self.process_current_file)
        self.process_button.pack(pady=(0, 10))
        
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
        """Setup quick category selection buttons from target folder."""
        button_frame = ttk.LabelFrame(parent, text="Quick Categories")
        button_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollable frame for categories
        canvas = tk.Canvas(button_frame, height=200)
        scrollbar = ttk.Scrollbar(button_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
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

        # Create buttons in grid
        cols = 2
        for i, category in enumerate(categories):
            row = i // cols
            col = i % cols
            btn = ttk.Button(scrollable_frame, text=category,
                           command=lambda c=category: self.select_category(c))
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
            
        # Configure column weights
        for i in range(cols):
            scrollable_frame.columnconfigure(i, weight=1)
            
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
            
    def load_media(self, file_path: str, completion_callback: Optional[Callable] = None):
        """Load and display media file."""
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
            self.load_image(file_path)

        # Set focus to main window (not textbox) so keyboard shortcuts work immediately
        self.root.focus_set()
        
    def load_image(self, file_path: str):
        """Load and display an image file with responsive sizing."""
        try:
            # Hide video controls
            self.controls_frame.pack_forget()
            
            # Load original image
            image = Image.open(file_path)
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
            
            # Load image again
            image = Image.open(self.current_file_path)
            
            # Calculate scaling to fit area while maintaining aspect ratio
            # Never scale above 100% of original size
            scale_x = min(display_width / image.width, 1.0)
            scale_y = min(display_height / image.height, 1.0) 
            scale = min(scale_x, scale_y)
            
            new_width = int(image.width * scale)
            new_height = int(image.height * scale)
            
            # Resize image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.current_image = ImageTk.PhotoImage(image)
            
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
        """Load and prepare video for playback."""
        try:
            # Show video controls
            self.controls_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # For now, show video info and thumbnail
            self.media_label.configure(image="", text=f"Video file:\n{os.path.basename(file_path)}\n\nUse controls below to play")
            
            
        except Exception as e:
            logging.error(f"Error loading video: {e}")
            self.media_label.configure(image="", text=f"Error loading video:\n{str(e)}")
            
    def clear_media(self):
        """Clear current media display."""
        self.current_image = None
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
            self.play_button.configure(text="Pause")
            
    def pause_video(self):
        """Pause video playback."""
        self.video_playing = False
        self.video_paused = True
        self.play_button.configure(text="Play")
        
    def stop_video(self):
        """Stop video playback."""
        self.video_playing = False
        self.video_paused = False
        self.play_button.configure(text="Play")
        self.video_progress.set(0)
        
    def seek_video(self, value):
        """Seek to position in video."""
        if self.current_file_path and is_video_file(self.current_file_path):
            logging.info(f"Seeking to {float(value):.1f}%")
        
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


def show_media_viewer(file_path: str, target_folder: str, completion_callback: Optional[Callable] = None):
    """Show the media viewer for a specific file."""
    root = tk.Tk()
    viewer = MediaViewer(root, target_folder)
    viewer.load_media(file_path, completion_callback)
    
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