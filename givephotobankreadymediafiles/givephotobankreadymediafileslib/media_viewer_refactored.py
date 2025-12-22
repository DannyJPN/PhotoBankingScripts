"""
Refactored MediaViewer - Modular architecture.

Main orchestrator that coordinates all modules to provide the media viewing and metadata
generation interface. This is a refactored version with separated concerns for better
maintainability.
"""

import os
import sys
import logging
import subprocess
import platform
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable, List, Dict
import pygame

from givephotobankreadymediafileslib.constants import STATUS_REJECTED
from givephotobankreadymediafileslib.viewer_state import ViewerState
from givephotobankreadymediafileslib.media_display import MediaDisplay
from givephotobankreadymediafileslib.categories_manager import CategoriesManager
from givephotobankreadymediafileslib.ui_components import UIComponents
from givephotobankreadymediafileslib.ai_coordinator import AICoordinator
from givephotobankreadymediafileslib.metadata_validator import MetadataValidator


class MediaViewerRefactored:
    """
    Refactored media viewer with modular architecture.

    Coordinates 7 specialized modules:
    - ViewerState: Input state and character counters
    - MediaDisplay: Image/video display logic
    - CategoriesManager: Photobank category management
    - UIComponents: UI layout and debouncing
    - AICoordinator: AI generation and threading
    - MetadataValidator: Button state and validation
    """

    def __init__(self, root: tk.Tk, target_folder: str, categories: Dict[str, List[str]] = None):
        """
        Initialize MediaViewerRefactored.

        Args:
            root: Tkinter root window
            target_folder: Target folder path (legacy parameter, unused)
            categories: Dictionary mapping photobank names to category lists
        """
        self.root = root
        self.root.title("AI Media Metadata Generator")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        # Initialize pygame for video playback
        pygame.init()
        pygame.mixer.init()

        # Create module instances
        self.viewer_state = ViewerState(root)
        self.media_display = MediaDisplay(root)
        self.categories_manager = CategoriesManager(root, categories)
        self.ui_components = UIComponents(root)
        self.ai_coordinator = AICoordinator(root, self.viewer_state, self.categories_manager, self.ui_components)
        self.metadata_validator = MetadataValidator(
            self.viewer_state, self.ui_components, self.ai_coordinator, self.categories_manager
        )

        # Wire up cross-module references
        self._wire_modules()

        # Setup UI
        self.ui_components.setup_styles()
        self._setup_ui_with_callbacks()

        # Bind resize event for responsive image display
        self.root.bind('<Configure>', self.media_display.on_window_resize)

        # Handle window close event (equivalent to Ctrl+C)
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Load AI models after GUI is ready
        self.root.after(500, self.ai_coordinator.load_ai_models)

    def _wire_modules(self):
        """Wire up cross-module dependencies and callbacks."""
        # ViewerState needs button update callback (debounced)
        self.viewer_state.update_button_states_callback = self.ui_components.update_all_button_states_debounced

        # UIComponents needs button update callback (actual update logic)
        self.ui_components.set_button_update_callback(self.metadata_validator.update_all_button_states)

        # AICoordinator needs callbacks to validator
        self.ai_coordinator.update_all_button_states_callback = self.metadata_validator.update_all_button_states
        self.ai_coordinator.should_enable_generation_button_callback = self.metadata_validator.should_enable_generation_button

        # AICoordinator needs photobank categories
        self.ai_coordinator.photobank_categories = self.categories_manager.categories

    def _setup_ui_with_callbacks(self):
        """Setup UI with all necessary callbacks."""
        # Media panel callbacks
        media_callbacks = {
            'toggle_video': self.media_display.toggle_video,
            'stop_video': self.media_display.stop_video,
            'seek_video': self.media_display.seek_video
        }

        # Metadata panel callbacks
        metadata_callbacks = {
            # State handlers
            'on_title_change': self.viewer_state.on_title_change,
            'on_title_focus_out': self.viewer_state.on_title_focus_out,
            'on_description_change': self.viewer_state.on_description_change,
            'on_description_focus_out': self.viewer_state.on_description_focus_out,
            'on_keywords_change': self.viewer_state.on_keywords_change,
            'on_keywords_focus_out': self.viewer_state.on_keywords_focus_out,
            'handle_title_input': self.viewer_state.handle_title_input,
            # AI generation
            'generate_title': self.ai_coordinator.generate_title,
            'generate_description': self.ai_coordinator.generate_description,
            'generate_keywords': self.ai_coordinator.generate_keywords,
            'generate_categories': self.ai_coordinator.generate_categories,
            'generate_all_metadata': self.ai_coordinator.generate_all_metadata,
            # Model selection
            'on_model_selected': self.on_model_selected,
            # Actions
            'save_metadata': self.save_metadata,
            'reject_metadata': self.reject_metadata,
            'open_in_explorer': self.open_in_explorer
        }

        # Setup UI
        self.ui_components.setup_ui(media_callbacks, metadata_callbacks)

        # Wire widget references between modules
        self._wire_widget_references()

        # Populate categories UI
        self.categories_manager.populate_categories_ui()

    def _wire_widget_references(self):
        """Wire widget references from ui_components to other modules."""
        # ViewerState widgets
        self.viewer_state.title_entry = self.ui_components.title_entry
        self.viewer_state.desc_text = self.ui_components.desc_text
        self.viewer_state.keywords_tag_entry = self.ui_components.keywords_tag_entry
        self.viewer_state.editorial_var = self.ui_components.editorial_var
        self.viewer_state.title_char_label = self.ui_components.title_char_label
        self.viewer_state.desc_char_label = self.ui_components.desc_char_label
        # Note: keywords_count_label removed - TagEntry has built-in counter

        # MediaDisplay widgets
        self.media_display.media_label = self.ui_components.media_label
        self.media_display.controls_frame = self.ui_components.controls_frame
        self.media_display.play_button = self.ui_components.play_button
        self.media_display.stop_button = self.ui_components.stop_button
        self.media_display.video_progress = self.ui_components.video_progress
        self.media_display.time_label = self.ui_components.time_label

        # CategoriesManager widgets
        self.categories_manager.categories_container = self.ui_components.categories_container

    def on_model_selected(self, event=None):
        """Handle model selection change."""
        selection = self.ui_components.model_combo.get()
        logging.debug(f"AI model selected: {selection}")
        # Update button states when model changes
        self.metadata_validator.update_all_button_states()

    def load_media(self, file_path: str, record: dict, completion_callback: Optional[Callable] = None):
        """
        Load and display media file with metadata interface.

        Args:
            file_path: Path to media file
            record: CSV record dictionary with existing metadata
            completion_callback: Callback to invoke when user saves or rejects
        """
        # Store file info in viewer state
        self.viewer_state.current_file_path = file_path
        self.viewer_state.current_record = record
        self.viewer_state.completion_callback = completion_callback

        # Clear previous media
        self.media_display.clear_media()

        # Update file path display
        self.ui_components.file_path_label.configure(text=file_path)

        # Load existing metadata from record
        self.viewer_state.load_metadata_from_record(record)

        # Load existing categories from record
        self.categories_manager.load_existing_categories(record)

        # Load media file
        self.media_display.load_media(file_path)

        # Update button states after loading file and metadata
        self.metadata_validator.update_all_button_states()

        # Focus on first control
        self.viewer_state.title_entry.focus()

    def save_metadata(self):
        """Save metadata and close window."""
        # Improved validation - check both attribute existence and value
        if not hasattr(self.viewer_state, 'current_record') or self.viewer_state.current_record is None:
            messagebox.showwarning("No File", "No file is currently loaded.")
            return

        # Collect metadata from viewer state
        metadata = self.viewer_state.collect_metadata()

        title = metadata.get('title', '')
        if not title:
            messagebox.showwarning("Missing Data", "Please enter a title.")
            return

        # Collect selected categories
        selected_categories = self.categories_manager.collect_selected_categories()

        # Get selected AI model
        selected_model = self.ui_components.model_combo.get()

        # Build complete metadata dictionary
        complete_metadata = {
            'title': metadata['title'],
            'description': metadata['description'],
            'keywords': metadata['keywords'],
            'editorial': metadata['editorial'],
            'categories': selected_categories,
            'ai_model': selected_model  # Pass selected model for alternative generation
        }

        # Call completion callback with metadata and check return value
        save_success = True
        if self.viewer_state.completion_callback:
            save_success = self.viewer_state.completion_callback(complete_metadata)

            # If callback returns None (old behavior), assume success
            if save_success is None:
                save_success = True

        # Only close window if save succeeded
        if save_success:
            self.root.destroy()
        else:
            messagebox.showerror(
                "Save Failed",
                "Failed to save metadata to CSV file.\n\n"
                "Please check:\n"
                "• CSV file exists and is not locked\n"
                "• You have write permissions\n"
                "• Dropbox is not syncing the file\n\n"
                "Check logs for details."
            )
            logging.error("Save failed - window remains open for retry")

    def reject_metadata(self):
        """Reject this file and set status to rejected for all photobanks."""
        if not hasattr(self.viewer_state, 'current_record'):
            messagebox.showwarning("No File", "No file is currently loaded.")
            return

        # Ask for confirmation
        response = messagebox.askyesno(
            "Reject File",
            f"Are you sure you want to reject this file?\n\n{self.viewer_state.current_file_path}\n\n"
            f"This will set status to '{STATUS_REJECTED}' for all photobanks.",
            icon='warning'
        )

        if not response:
            return

        # Create rejection metadata (minimal data needed)
        metadata = {
            'title': '',
            'description': '',
            'keywords': '',
            'editorial': False,
            'categories': {},
            'rejected': True  # Special flag to indicate rejection
        }

        # Call completion callback with rejection metadata
        if self.viewer_state.completion_callback:
            self.viewer_state.completion_callback(metadata)

        self.root.destroy()

    def open_in_explorer(self):
        """Open the current file location in Windows Explorer."""
        if not self.viewer_state.current_file_path:
            messagebox.showwarning("No File", "No file is currently loaded.")
            return

        try:
            if platform.system() == "Windows":
                # Normalize path to use backslashes for Windows Explorer
                normalized_path = os.path.normpath(self.viewer_state.current_file_path)
                # Use Windows Explorer to show file and select it
                # Don't use check=True as Explorer sometimes returns non-zero exit codes even on success
                result = subprocess.run(['explorer', '/select,', normalized_path])
                logging.debug(f"Opened file location in Explorer: {normalized_path} (exit code: {result.returncode})")
            else:
                # For other systems, just open the directory
                directory = os.path.dirname(self.viewer_state.current_file_path)
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(['open', directory])
                else:  # Linux and others
                    subprocess.run(['xdg-open', directory])
                logging.debug(f"Opened directory: {directory}")

        except Exception as e:
            logging.error(f"Failed to open file location: {e}")
            messagebox.showerror("Error", f"Failed to open file location:\n{str(e)}")

    def on_window_close(self):
        """Handle window close event - equivalent to Ctrl+C."""
        logging.debug("Window closed by user - terminating script")
        self.root.destroy()

        # Exit the entire script (equivalent to Ctrl+C)
        sys.exit(0)


def show_media_viewer(file_path: str, record: dict, completion_callback: Optional[Callable] = None,
                     categories: Dict[str, List[str]] = None):
    """
    Show the media viewer for a specific file and record.

    Args:
        file_path: Path to media file
        record: CSV record dictionary
        completion_callback: Callback when user saves or rejects
        categories: Photobank categories dictionary
    """
    root = tk.Tk()
    viewer = MediaViewerRefactored(root, "", categories)  # Pass categories to viewer
    viewer.load_media(file_path, record, completion_callback)

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
        show_media_viewer(test_file, {}, None, {})
    else:
        print("Usage: python media_viewer_refactored.py <media_file>")