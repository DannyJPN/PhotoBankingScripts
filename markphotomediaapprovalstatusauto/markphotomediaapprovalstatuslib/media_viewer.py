"""
Media viewer with approval controls for multiple photobanks.
Based on sortunsortedmedia MediaViewer structure.
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import pygame
from typing import Optional, Callable, List, Dict, Tuple
import threading
import time

from markphotomediaapprovalstatuslib.constants import (
    BANKS, STATUS_CHECKED, STATUS_APPROVED, STATUS_REJECTED, STATUS_MAYBE, 
    STATUS_COLUMN_KEYWORD
)
from markphotomediaapprovalstatuslib.media_helper import is_video_file, is_jpg_file


class MediaViewer:
    """Media viewer for approval workflow with multiple photobank controls."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Media Approval Viewer")
        self.root.geometry("1600x900")
        self.root.minsize(1000, 700)
        
        # Initialize pygame for video playback
        pygame.init()
        pygame.mixer.init()
        
        # Current media info
        self.current_file_path: Optional[str] = None
        self.current_record: Optional[Dict[str, str]] = None
        self.current_image: Optional[ImageTk.PhotoImage] = None
        self.original_image_size: Optional[tuple] = None
        self.video_surface = None
        self.video_playing = False
        self.video_paused = False
        self.completion_callback: Optional[Callable] = None
        
        # Approval controls data
        self.bank_vars: Dict[str, tk.StringVar] = {}
        
        self.setup_ui()
        
        # Bind resize event for responsive image display
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        
    def setup_ui(self):
        """Setup the main UI layout."""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for media display
        self.setup_media_panel(main_paned)
        
        # Right panel for approval interface
        self.setup_approval_panel(main_paned)
        
    def setup_media_panel(self, parent):
        """Setup the left panel for media display."""
        media_frame = ttk.Frame(parent)
        parent.add(media_frame, weight=1)
        
        # Media display area
        self.media_label = ttk.Label(media_frame, text="No media loaded", 
                                   anchor=tk.CENTER, background='black', foreground='white')
        self.media_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
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
        
    def setup_approval_panel(self, parent):
        """Setup the right panel with approval interface."""
        control_frame = ttk.Frame(parent)
        parent.add(control_frame, weight=1)
        
        # File path display
        path_frame = ttk.LabelFrame(control_frame, text="Current File")
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.file_path_label = ttk.Label(path_frame, text="No file loaded", 
                                       wraplength=400, justify=tk.LEFT, font=('TkDefaultFont', 10, 'bold'))
        self.file_path_label.pack(padx=10, pady=10, anchor=tk.W)
        
        # Media info display
        info_frame = ttk.LabelFrame(control_frame, text="Media Information")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.title_label = ttk.Label(info_frame, text="Title: ", 
                                   wraplength=300, justify=tk.LEFT)
        self.title_label.pack(padx=10, pady=2, anchor=tk.W)
        
        self.description_label = ttk.Label(info_frame, text="Description: ", 
                                         wraplength=300, justify=tk.LEFT)
        self.description_label.pack(padx=10, pady=2, anchor=tk.W)
        
        # Approval controls frame
        approval_frame = ttk.LabelFrame(control_frame, text="Bank Approval Status")
        approval_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create container frame to limit width
        container_frame = ttk.Frame(approval_frame)
        container_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame for bank controls with fixed width
        canvas = tk.Canvas(container_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Process button
        process_frame = ttk.Frame(control_frame)
        process_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.process_button = ttk.Button(process_frame, text="Process File", 
                                       command=self.process_current_file)
        self.process_button.pack(pady=10)
        
    def load_media(
        self,
        file_path: str,
        record: Dict[str, str],
        completion_callback: Optional[Callable] = None,
        target_bank: Optional[str] = None
    ):
        """
        Load and display media file with approval controls.

        Args:
            file_path: Path to media file
            record: CSV record dictionary
            completion_callback: Callback function to receive user decision
            target_bank: If specified, show controls for this bank only (bank-first mode).
                        If None, show all banks with "kontrolováno" status (legacy mode).
        """
        self.current_file_path = file_path
        self.current_record = record
        self.completion_callback = completion_callback

        # Clear previous media
        self.clear_media()

        # Update file path display
        self.file_path_label.configure(text=file_path)

        # Update media info
        title = record.get('Název', '')
        description = record.get('Popis', '')
        self.title_label.configure(text=f"Title: {title}")
        self.description_label.configure(text=f"Description: {description}")

        # Determine which banks to show
        banks_to_show = []

        if target_bank:
            # Bank-first mode: show only target bank if it has "kontrolováno" status
            status_column = f"{target_bank} {STATUS_COLUMN_KEYWORD}"
            if status_column in record and record[status_column] == STATUS_CHECKED:
                banks_to_show = [target_bank]
            else:
                logging.warning(f"Target bank {target_bank} does not have 'kontrolováno' status for this file")
        else:
            # Legacy mode: show all banks with "kontrolováno" status
            for bank in BANKS:
                status_column = f"{bank} {STATUS_COLUMN_KEYWORD}"
                if status_column in record and record[status_column] == STATUS_CHECKED:
                    banks_to_show.append(bank)

        if not banks_to_show:
            messagebox.showinfo("No Banks", "No banks with 'kontrolováno' status found for this file.")
            return

        # Create controls for these banks
        self.create_bank_controls(banks_to_show)

        # Load media file
        if is_video_file(file_path):
            self.load_video(file_path)
        else:
            self.load_image(file_path)

        # Focus on first control
        if self.bank_vars:
            self.root.focus()
            
    def create_bank_controls(self, banks_to_show: List[str]):
        """Create approval controls for specified banks."""
        # Clear existing controls
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.bank_vars.clear()
        
        # Configure columns to expand equally with uniform width
        self.scrollable_frame.columnconfigure(0, weight=1, uniform="bank_columns")
        self.scrollable_frame.columnconfigure(1, weight=1, uniform="bank_columns")
        
        # Place banks in 2 columns
        row = 0
        col = 0
        for i, bank in enumerate(banks_to_show):
            # Bank frame
            bank_frame = ttk.LabelFrame(self.scrollable_frame, text=bank)
            bank_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            
            # Radio button variable
            bank_var = tk.StringVar(value="")
            self.bank_vars[bank] = bank_var
            
            # Radio buttons
            radio_frame = ttk.Frame(bank_frame)
            radio_frame.pack(fill=tk.X, padx=5, pady=5)
            
            clear_radio = ttk.Radiobutton(radio_frame, text="None",
                                        variable=bank_var, value="")
            clear_radio.pack(side=tk.LEFT, padx=5)

            approved_radio = ttk.Radiobutton(radio_frame, text="Approved",
                                           variable=bank_var, value=STATUS_APPROVED)
            approved_radio.pack(side=tk.LEFT, padx=5)

            rejected_radio = ttk.Radiobutton(radio_frame, text="Rejected",
                                           variable=bank_var, value=STATUS_REJECTED)
            rejected_radio.pack(side=tk.LEFT, padx=5)

            maybe_radio = ttk.Radiobutton(radio_frame, text="Approved?", 
                                        variable=bank_var, value=STATUS_MAYBE)
            maybe_radio.pack(side=tk.LEFT, padx=5)
            
            # Move to next position (2 columns layout)
            col += 1
            if col >= 2:
                col = 0
                row += 1
            
            
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
        
    def process_current_file(self):
        """Process the current file with selected approvals."""
        if not self.current_record:
            messagebox.showwarning("No File", "No file is currently loaded.")
            return

        # Collect approval decisions
        decisions = {}

        for bank, var in self.bank_vars.items():
            decision = var.get()
            if decision:  # Only process if user made a selection
                decisions[bank] = decision

        # Call completion callback
        if self.completion_callback:
            # If single bank (bank-first mode), return just the decision value
            # If multiple banks (legacy mode), return dict
            if len(self.bank_vars) == 1:
                # Single bank mode: return just the decision string
                single_decision = next(iter(decisions.values())) if decisions else None
                self.completion_callback(single_decision)
            else:
                # Multiple banks mode: return dict
                self.completion_callback(decisions)

        self.root.destroy()
        
    def on_window_close(self):
        """Handle window close event - signal cancellation to caller."""
        logging.info("Approval window closed by user - cancelling operation")
        self.root.destroy()

        # Signal cancellation through callback instead of killing process
        if self.completion_callback:
            self.completion_callback(None)  # None signals user cancellation


def show_media_viewer(
    file_path: str,
    record: Dict[str, str],
    completion_callback: Optional[Callable] = None,
    target_bank: Optional[str] = None
):
    """
    Show the media viewer for a specific file and record.

    Args:
        file_path: Path to media file
        record: CSV record dictionary
        completion_callback: Callback function to receive user decision
        target_bank: If specified, show controls for this bank only (bank-first mode).
                    If None, show all banks with "kontrolováno" status (legacy mode).
    """
    root = tk.Tk()
    viewer = MediaViewer(root)
    viewer.load_media(file_path, record, completion_callback, target_bank=target_bank)

    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    # Test the viewer
    test_record = {
        'Soubor': 'test.jpg',
        'Cesta': 'C:/test.jpg',
        'Název': 'Test Image',
        'Popis': 'Test description',
        'ShutterStock status': 'kontrolováno',
        'AdobeStock status': 'kontrolováno'
    }
    
    def test_callback(decisions):
        print(f"Decisions made: {decisions}")
        
    show_media_viewer(test_record.get('Cesta', ''), test_record, test_callback)