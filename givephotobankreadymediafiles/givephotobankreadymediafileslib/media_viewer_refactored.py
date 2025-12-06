"""
Graphical media viewer with responsive layout for categorizing files.

This is the main orchestrator that coordinates all viewer components.
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, List, Dict
import threading
import subprocess
import platform

# Import refactored modules
from givephotobankreadymediafileslib import media_display
from givephotobankreadymediafileslib import ai_coordinator
from givephotobankreadymediafileslib import categories_manager
from givephotobankreadymediafileslib import metadata_validator
from givephotobankreadymediafileslib import ui_components
from givephotobankreadymediafileslib import viewer_state

# Import existing dependencies
from givephotobankreadymediafileslib.media_helper import is_video_file
from givephotobankreadymediafileslib.tag_entry import TagEntry
from givephotobankreadymediafileslib.editorial_dialog import (
    get_editorial_metadata, extract_editorial_metadata_from_exif
)


class MediaViewer:
    """
    Main media viewer orchestrator class.

    This class coordinates UI components, state management, and AI generation.
    """

    def __init__(self, root: tk.Tk, target_folder: str, categories: Dict[str, List[str]] = None):
        """
        Initialize the media viewer.

        :param root: Tkinter root window
        :param target_folder: Target folder for media files
        :param categories: Dict of photobank -> list of categories
        """
        self.root = root
        self.root.title("AI Media Metadata Generator")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        # Store categories
        self.categories = categories or {}

        # Initialize pygame for video playback
        media_display.initialize_pygame()

        # Initialize state
        self.state = viewer_state.create_initial_state()

        # AI generation state
        self.ai_threads = {
            'title': None,
            'description': None,
            'keywords': None,
            'categories': None,
            'all': None
        }
        self.ai_cancelled = {
            'title': False,
            'description': False,
            'keywords': False,
            'categories': False
        }
        self.generation_lock = threading.Lock()
        self._generate_all_active = False

        # Configure styles
        ui_components.setup_ttk_styles()

        # Setup UI
        self.setup_ui()

        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)

        # Handle window close event
        ui_components.set_window_protocol(self.root, "WM_DELETE_WINDOW", self.on_window_close)

    def setup_ui(self):
        """Setup the main UI layout."""
        # Create main paned window
        main_paned = ui_components.create_paned_window(self.root, orient=tk.HORIZONTAL)
        ui_components.pack_widget(main_paned, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel for media display
        self.setup_media_panel(main_paned)

        # Right panel for metadata interface
        self.setup_metadata_panel(main_paned)

    def setup_media_panel(self, parent):
        """
        Setup the left panel for media display.

        :param parent: Parent paned window
        """
        media_frame = ui_components.create_frame(parent)
        parent.add(media_frame, weight=2)

        # Media display area
        self.media_label = ui_components.create_label(
            media_frame,
            text="No media loaded"
        )
        ui_components.configure_widget(
            self.media_label,
            anchor=tk.CENTER,
            background='black',
            foreground='white'
        )
        ui_components.pack_widget(self.media_label, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Video controls frame
        controls_frame = ui_components.create_frame(media_frame)
        ui_components.pack_widget(controls_frame, fill=tk.X, padx=5, pady=5)

        self.play_button = ui_components.create_button(
            controls_frame,
            text="Play",
            command=self.toggle_video
        )
        ui_components.pack_widget(self.play_button, side=tk.LEFT, padx=2)

        self.stop_button = ui_components.create_button(
            controls_frame,
            text="Stop",
            command=self.stop_video
        )
        ui_components.pack_widget(self.stop_button, side=tk.LEFT, padx=2)

        # Video progress bar
        self.video_progress = ui_components.create_scale(
            controls_frame,
            orient=tk.HORIZONTAL,
            from_=0,
            to=100,
            command=self.seek_video
        )
        ui_components.pack_widget(self.video_progress, side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Time label
        self.time_label = ui_components.create_label(controls_frame, text="00:00 / 00:00")
        ui_components.pack_widget(self.time_label, side=tk.RIGHT, padx=2)

        # Initially hide video controls
        controls_frame.pack_forget()
        self.controls_frame = controls_frame

    def setup_metadata_panel(self, parent):
        """
        Setup the right panel with metadata interface.

        :param parent: Parent paned window
        """
        control_frame = ui_components.create_frame(parent)
        parent.add(control_frame, weight=1)

        # Create horizontal paned window
        metadata_paned = ui_components.create_paned_window(control_frame, orient=tk.HORIZONTAL)
        ui_components.pack_widget(metadata_paned, fill=tk.BOTH, expand=True, pady=(0, 0))

        # Left side - metadata fields
        left_frame = ui_components.create_frame(metadata_paned)
        metadata_paned.add(left_frame, weight=3)

        # Right side - keywords listbox
        right_frame = ui_components.create_frame(metadata_paned)
        metadata_paned.add(right_frame, weight=2)

        # File path display
        self.setup_file_path_panel(left_frame)

        # AI Model Selection
        self.setup_ai_model_panel(left_frame)

        # Title input
        self.setup_title_panel(left_frame)

        # Description input
        self.setup_description_panel(left_frame)

        # Keywords
        self.setup_keywords_panel(right_frame)

        # Editorial checkbox
        self.setup_editorial_panel(left_frame)

        # Categories selection
        self.setup_categories_panel(control_frame)

        # Action buttons
        self.setup_action_buttons(control_frame)

    def setup_file_path_panel(self, parent):
        """
        Setup file path display panel.

        :param parent: Parent frame
        """
        path_frame = ui_components.create_labeled_frame(parent, text="Current File")
        ui_components.pack_widget(path_frame, fill=tk.X, padx=5, pady=(5, 2))

        self.file_path_label = ui_components.create_label(
            path_frame,
            text="No file loaded",
            wraplength=250,
            justify=tk.LEFT
        )
        ui_components.pack_widget(self.file_path_label, padx=10, pady=5, anchor=tk.W)

    def setup_ai_model_panel(self, parent):
        """
        Setup AI model selection panel.

        :param parent: Parent frame
        """
        model_frame = ui_components.create_labeled_frame(parent, text="AI Model Selection")
        ui_components.pack_widget(model_frame, fill=tk.X, padx=5, pady=(2, 2))

        # Model selection dropdown
        selection_frame = ui_components.create_frame(model_frame)
        ui_components.pack_widget(selection_frame, fill=tk.X, padx=10, pady=5)

        label = ui_components.create_label(selection_frame, text="Model:")
        ui_components.pack_widget(label, side=tk.LEFT, padx=(0, 5))

        self.model_combo = ui_components.create_combobox(
            selection_frame,
            values=[],
            state="readonly",
            width=30
        )
        ui_components.pack_widget(self.model_combo, side=tk.LEFT, fill=tk.X, expand=True)

        # Load AI models after GUI is ready
        self.root.after(500, self.load_ai_models)

    def setup_title_panel(self, parent):
        """
        Setup title input panel.

        :param parent: Parent frame
        """
        title_frame = ui_components.create_labeled_frame(parent, text="Title")
        ui_components.pack_widget(title_frame, fill=tk.X, padx=5, pady=(2, 2))

        label = ui_components.create_label(title_frame, text="Enter title:")
        ui_components.pack_widget(label, anchor=tk.W, padx=10, pady=(5, 3))

        self.title_entry = ui_components.create_entry(title_frame, width=30)
        ui_components.pack_widget(self.title_entry, fill=tk.X, padx=10, pady=(0, 5))
        ui_components.bind_key_event(self.title_entry, '<KeyRelease>', self.on_title_change)
        ui_components.bind_key_event(self.title_entry, '<Return>', self.handle_title_input)

        # Title controls
        title_controls_frame = ui_components.create_frame(title_frame)
        ui_components.pack_widget(title_controls_frame, fill=tk.X, padx=10, pady=(0, 5))

        self.title_char_label = ui_components.create_label(title_controls_frame, text="0/80")
        ui_components.pack_widget(self.title_char_label, side=tk.LEFT)

        self.title_generate_button = ui_components.create_button(
            title_controls_frame,
            text="Generate",
            command=self.generate_title
        )
        ui_components.pack_widget(self.title_generate_button, side=tk.RIGHT)

    def setup_description_panel(self, parent):
        """
        Setup description input panel.

        :param parent: Parent frame
        """
        desc_frame = ui_components.create_labeled_frame(parent, text="Description")
        ui_components.pack_widget(desc_frame, fill=tk.X, padx=5, pady=(2, 2))

        label = ui_components.create_label(desc_frame, text="Enter description:")
        ui_components.pack_widget(label, anchor=tk.W, padx=10, pady=(5, 3))

        self.desc_text = ui_components.create_text(
            desc_frame,
            height=4,
            width=30,
            wrap=tk.WORD,
            font=('Arial', 9)
        )
        ui_components.pack_widget(self.desc_text, fill=tk.X, padx=10, pady=(0, 5))
        ui_components.bind_key_event(self.desc_text, '<KeyRelease>', self.on_description_change)

        # Description controls
        desc_controls_frame = ui_components.create_frame(desc_frame)
        ui_components.pack_widget(desc_controls_frame, fill=tk.X, padx=10, pady=(0, 5))

        self.desc_char_label = ui_components.create_label(desc_controls_frame, text="0/200")
        ui_components.pack_widget(self.desc_char_label, side=tk.LEFT)

        self.desc_generate_button = ui_components.create_button(
            desc_controls_frame,
            text="Generate",
            command=self.generate_description
        )
        ui_components.pack_widget(self.desc_generate_button, side=tk.RIGHT)

    def setup_keywords_panel(self, parent):
        """
        Setup keywords panel.

        :param parent: Parent frame
        """
        keywords_frame = ui_components.create_labeled_frame(parent, text="Keywords (Tags)")
        ui_components.pack_widget(keywords_frame, fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))

        # TagEntry widget
        self.keywords_tag_entry = TagEntry(
            keywords_frame,
            width=25,
            max_tags=50,
            on_change=self.on_keywords_change
        )
        ui_components.pack_widget(self.keywords_tag_entry, fill=tk.BOTH, expand=True, padx=10, pady=(5, 5))

        # Keywords controls
        keywords_controls_frame = ui_components.create_frame(keywords_frame)
        ui_components.pack_widget(keywords_controls_frame, fill=tk.X, padx=10, pady=(0, 5))

        self.keywords_count_label = ui_components.create_label(keywords_controls_frame, text="0/50")
        ui_components.pack_widget(self.keywords_count_label, side=tk.LEFT)

        self.keywords_generate_button = ui_components.create_button(
            keywords_controls_frame,
            text="Generate",
            command=self.generate_keywords
        )
        ui_components.pack_widget(self.keywords_generate_button, side=tk.RIGHT)

    def setup_editorial_panel(self, parent):
        """
        Setup editorial mode panel.

        :param parent: Parent frame
        """
        editorial_frame = ui_components.create_labeled_frame(parent, text="Editorial Mode")
        ui_components.pack_widget(editorial_frame, fill=tk.X, padx=5, pady=(2, 0))

        self.editorial_var = tk.BooleanVar()
        self.editorial_checkbox = ui_components.create_checkbutton(
            editorial_frame,
            text="Editorial mode",
            variable=self.editorial_var
        )
        ui_components.pack_widget(self.editorial_checkbox, anchor=tk.W, padx=10, pady=5)

    def setup_categories_panel(self, parent):
        """
        Setup categories selection panel.

        :param parent: Parent frame
        """
        categories_frame = ui_components.create_labeled_frame(parent, text="Categories")
        ui_components.pack_widget(categories_frame, fill=tk.X, padx=5, pady=(0, 5))

        # Categories input with generate button
        categories_input_frame = ui_components.create_frame(categories_frame)
        ui_components.pack_widget(categories_input_frame, fill=tk.X, padx=10, pady=(10, 5))

        label = ui_components.create_label(categories_input_frame, text="Select categories:")
        ui_components.pack_widget(label, side=tk.LEFT, padx=(0, 5))

        self.categories_generate_button = ui_components.create_button(
            categories_input_frame,
            text="Generate",
            command=self.generate_categories
        )
        ui_components.pack_widget(self.categories_generate_button, side=tk.RIGHT)

        # Container for categories
        self.categories_container = ui_components.create_frame(categories_frame)
        ui_components.pack_widget(self.categories_container, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Populate categories
        self.populate_categories_ui()

    def setup_action_buttons(self, parent):
        """
        Setup action buttons panel.

        :param parent: Parent frame
        """
        action_frame = ui_components.create_frame(parent)
        ui_components.pack_widget(action_frame, fill=tk.X, padx=5, pady=10, side=tk.BOTTOM)

        self.generate_all_button = ui_components.create_button(
            action_frame,
            text="Generate All",
            command=self.generate_all_metadata
        )
        ui_components.pack_widget(self.generate_all_button, side=tk.LEFT, padx=2)

        self.save_button = ui_components.create_button(
            action_frame,
            text="Save & Continue",
            command=self.save_metadata
        )
        ui_components.pack_widget(self.save_button, side=tk.LEFT, padx=2)

        self.reject_button = ui_components.create_button(
            action_frame,
            text="Reject",
            command=self.reject_metadata,
            style='Reject.TButton'
        )
        ui_components.pack_widget(self.reject_button, side=tk.LEFT, padx=2)

        self.explorer_button = ui_components.create_button(
            action_frame,
            text="Open in Explorer",
            command=self.open_in_explorer
        )
        ui_components.pack_widget(self.explorer_button, side=tk.LEFT, padx=2)

    def populate_categories_ui(self):
        """Populate categories UI with dropdown lists for each photobank."""
        self.category_combos = {}

        if not self.categories:
            label = ui_components.create_label(self.categories_container, text="No categories available")
            ui_components.pack_widget(label, pady=10)
            return

        # Filter photobanks with categories
        photobanks_with_categories = categories_manager.filter_photobanks_with_categories(self.categories)

        if not photobanks_with_categories:
            label = ui_components.create_label(self.categories_container, text="No categories available")
            ui_components.pack_widget(label, pady=10)
            return

        # Horizontal layout
        row_frame = ui_components.create_frame(self.categories_container)
        ui_components.pack_widget(row_frame, fill=tk.X, pady=5)

        for photobank, categories in photobanks_with_categories:
            # Create comboboxes for this photobank
            combos = categories_manager.create_category_comboboxes(
                row_frame,
                photobank,
                categories
            )
            self.category_combos[photobank] = combos

    def load_media(self, file_path: str, record: dict, completion_callback: Optional[Callable] = None):
        """
        Load and display media file with metadata interface.

        :param file_path: Path to media file
        :param record: CSV record for file
        :param completion_callback: Callback to call when metadata is saved
        """
        self.state.current_file_path = file_path
        self.state.current_record = record
        self.state.completion_callback = completion_callback

        # Clear previous media
        self.clear_media()

        # Update file path display
        ui_components.configure_widget(self.file_path_label, text=file_path)

        # Load metadata from record
        self.state = viewer_state.load_state_from_record(self.state, record)

        # Create UI references
        ui_refs = viewer_state.UIReferences(
            title_entry=self.title_entry,
            desc_text=self.desc_text,
            keywords_tag_entry=self.keywords_tag_entry,
            editorial_var=self.editorial_var,
            model_combo=self.model_combo,
            file_path_label=self.file_path_label,
            media_label=self.media_label,
            controls_frame=self.controls_frame,
            category_combos=self.category_combos
        )

        # Sync UI from state
        viewer_state.sync_ui_from_state(self.state, ui_refs)

        # Update character counters
        self.on_title_change()
        self.on_description_change()

        # Load categories
        if hasattr(self, 'category_combos'):
            categories_manager.load_categories_from_record(self.category_combos, record)

        # Load media file
        if is_video_file(file_path):
            self.load_video(file_path)
        else:
            self.load_image(file_path)

        # Focus on first control
        self.title_entry.focus()

    def load_image(self, file_path: str):
        """
        Load and display an image file.

        :param file_path: Path to image file
        """
        try:
            # Hide video controls
            self.controls_frame.pack_forget()

            # Load and display image
            display_width, display_height = media_display.get_display_dimensions(self.media_label)
            self.state.current_image = media_display.display_image_in_label(
                self.media_label,
                file_path,
                display_width,
                display_height
            )

            # Store original size for resizing
            if self.state.current_image:
                _, self.state.original_image_size = media_display.load_image_file(file_path)

        except Exception as e:
            logging.error(f"Error loading image: {e}")
            ui_components.configure_widget(
                self.media_label,
                image="",
                text=f"Error loading image:\n{str(e)}"
            )

    def load_video(self, file_path: str):
        """
        Load and prepare video for playback.

        :param file_path: Path to video file
        """
        try:
            # Show video controls
            ui_components.pack_widget(self.controls_frame, fill=tk.X, padx=5, pady=5)

            # Display video placeholder
            media_display.display_video_placeholder(self.media_label, file_path)

        except Exception as e:
            logging.error(f"Error loading video: {e}")
            ui_components.configure_widget(
                self.media_label,
                image="",
                text=f"Error loading video:\n{str(e)}"
            )

    def resize_image(self):
        """Resize current image to fit display area responsively."""
        if not self.state.current_file_path or not self.state.original_image_size:
            return

        try:
            display_width, display_height = media_display.get_display_dimensions(self.media_label)
            self.state.current_image = media_display.display_image_in_label(
                self.media_label,
                self.state.current_file_path,
                display_width,
                display_height
            )
        except Exception as e:
            logging.error(f"Error resizing image: {e}")

    def clear_media(self):
        """Clear current media display."""
        self.state.current_image = None
        media_display.clear_media_display(self.media_label)
        self.stop_video()

    def toggle_video(self):
        """Toggle video play/pause."""
        if self.state.video_playing:
            self.pause_video()
        else:
            self.play_video()

    def play_video(self):
        """Start video playback."""
        if self.state.current_file_path and is_video_file(self.state.current_file_path):
            self.state.video_playing = True
            self.state.video_paused = False
            ui_components.configure_widget(self.play_button, text="Pause")

    def pause_video(self):
        """Pause video playback."""
        self.state.video_playing = False
        self.state.video_paused = True
        ui_components.configure_widget(self.play_button, text="Play")

    def stop_video(self):
        """Stop video playback."""
        self.state.video_playing = False
        self.state.video_paused = False
        ui_components.configure_widget(self.play_button, text="Play")
        self.video_progress.set(0)

    def seek_video(self, value):
        """
        Seek to position in video.

        :param value: Position value (0-100)
        """
        if self.state.current_file_path and is_video_file(self.state.current_file_path):
            logging.debug(f"Seeking to {float(value):.1f}%")

    def on_window_resize(self, event):
        """
        Handle window resize events.

        :param event: Tkinter event
        """
        # Only resize image if it's the main window being resized
        if event.widget == self.root and self.state.current_file_path:
            if not is_video_file(self.state.current_file_path):
                # Delay resize to avoid too many calls
                self.root.after(100, self.resize_image)

    def load_ai_models(self):
        """Load available AI models from configuration."""
        try:
            available_models = ai_coordinator.load_available_models()

            if not available_models:
                ui_components.configure_widget(
                    self.model_combo,
                    values=["No models available"]
                )
                self.model_combo.set("No models available")
                return

            # Populate combo box
            model_names = [model.display_name for model in available_models]
            ui_components.configure_widget(self.model_combo, values=model_names)

            # Set default model
            default_provider, default_model = ai_coordinator.get_default_model()
            default_key = f"{default_provider}/{default_model}"

            for i, model in enumerate(available_models):
                if model.key == default_key:
                    self.model_combo.current(i)
                    break
            else:
                if available_models:
                    self.model_combo.current(0)

            # Bind selection change
            ui_components.bind_key_event(self.model_combo, '<<ComboboxSelected>>', self.on_model_selected)

            self.on_model_selected()

        except Exception as e:
            logging.error(f"Error loading AI models: {e}")
            ui_components.configure_widget(
                self.model_combo,
                values=["Error loading models"]
            )
            self.model_combo.set("Error loading models")

    def on_model_selected(self, event=None):
        """
        Handle model selection change.

        :param event: Tkinter event
        """
        selection = self.model_combo.get()
        logging.debug(f"AI model selected: {selection}")

    def on_title_change(self, event=None):
        """
        Update title character counter.

        :param event: Tkinter event
        """
        title = self.title_entry.get()
        count = metadata_validator.count_title_characters(title)
        label_text = metadata_validator.format_character_count_label(count)
        label_color = metadata_validator.get_label_color(count)

        ui_components.configure_widget(self.title_char_label, text=label_text, foreground=label_color)

    def on_description_change(self, event=None):
        """
        Update description character counter.

        :param event: Tkinter event
        """
        description = self.desc_text.get('1.0', tk.END)
        count = metadata_validator.count_description_characters(description)
        label_text = metadata_validator.format_character_count_label(count)
        label_color = metadata_validator.get_label_color(count)

        ui_components.configure_widget(self.desc_char_label, text=label_text, foreground=label_color)

    def on_keywords_change(self):
        """Handle keywords change from TagEntry widget."""
        keywords = self.keywords_tag_entry.get_tags()
        count = metadata_validator.count_keywords(keywords)
        label_text = metadata_validator.format_character_count_label(count)
        label_color = metadata_validator.get_label_color(count)

        ui_components.configure_widget(self.keywords_count_label, text=label_text, foreground=label_color)

    def handle_title_input(self, event):
        """
        Handle title input Enter key.

        :param event: Tkinter event
        """
        self.desc_text.focus()

    def generate_title(self):
        """Generate title using AI in background thread."""
        if not self.state.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return

        selected_model = self.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return

        # Check if already running
        if ai_coordinator.is_thread_running(self.ai_threads['title']):
            self.ai_cancelled['title'] = True
            ui_components.configure_widget(self.title_generate_button, text="Generate", state="normal")
            self.ai_threads['title'] = None
            return

        # Start generation
        self.ai_cancelled['title'] = False
        ui_components.configure_widget(self.title_generate_button, text="Cancel")

        self.ai_threads['title'] = ai_coordinator.start_generation_thread(
            self._generate_title_worker,
            (selected_model,)
        )

    def _generate_title_worker(self, selected_model: str):
        """
        Worker thread for title generation.

        :param selected_model: Selected model display name
        """
        try:
            available_models = ai_coordinator.load_available_models()
            model_key = ai_coordinator.find_model_by_display_name(selected_model, available_models)

            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")

            if self.ai_cancelled['title']:
                self.root.after(0, self._update_title_result, None, None)
                return

            existing_title = self.title_entry.get().strip()
            title = ai_coordinator.generate_title_sync(
                self.state.current_file_path,
                model_key,
                existing_title if existing_title else None
            )

            if self.ai_cancelled['title']:
                self.root.after(0, self._update_title_result, None, None)
                return

            self.root.after(0, self._update_title_result, title, None)

        except Exception as e:
            logging.error(f"Title generation failed: {e}")
            self.root.after(0, self._update_title_result, None, str(e))

    def _update_title_result(self, title: Optional[str], error: Optional[str]):
        """
        Update UI with title generation result.

        :param title: Generated title
        :param error: Error message if failed
        """
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate title: {error}")
            elif title and not self.ai_cancelled['title']:
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, title)
                self.on_title_change()
        finally:
            if not ai_coordinator.is_thread_running(self.ai_threads['title']):
                ui_components.configure_widget(self.title_generate_button, text="Generate", state="normal")

    def generate_description(self):
        """Generate description using AI in background thread."""
        if not self.state.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return

        selected_model = self.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return

        # Check if already running
        if ai_coordinator.is_thread_running(self.ai_threads['description']):
            self.ai_cancelled['description'] = True
            ui_components.configure_widget(self.desc_generate_button, text="Generate", state="normal")
            self.ai_threads['description'] = None
            return

        # Start generation
        self.ai_cancelled['description'] = False
        ui_components.configure_widget(self.desc_generate_button, text="Cancel")

        self.ai_threads['description'] = ai_coordinator.start_generation_thread(
            self._generate_description_worker,
            (selected_model,)
        )

    def _generate_description_worker(self, selected_model: str):
        """
        Worker thread for description generation.

        :param selected_model: Selected model display name
        """
        try:
            available_models = ai_coordinator.load_available_models()
            model_key = ai_coordinator.find_model_by_display_name(selected_model, available_models)

            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")

            if self.ai_cancelled['description']:
                self.root.after(0, self._update_description_result, None, None)
                return

            # Handle editorial metadata if needed
            editorial_data = None
            if self.editorial_var.get():
                extracted_data, missing_fields = extract_editorial_metadata_from_exif(self.state.current_file_path)

                if any(missing_fields.values()):
                    editorial_data = self._show_editorial_dialog_sync(missing_fields, extracted_data)
                    if editorial_data is None:
                        return
                    editorial_data = {**extracted_data, **editorial_data}
                else:
                    editorial_data = extracted_data

            existing_title = self.title_entry.get().strip()
            existing_desc = self.desc_text.get('1.0', tk.END).strip()

            description = ai_coordinator.generate_description_sync(
                self.state.current_file_path,
                model_key,
                existing_title if existing_title else None,
                existing_desc if existing_desc else None,
                editorial_data
            )

            if self.ai_cancelled['description']:
                self.root.after(0, self._update_description_result, None, None)
                return

            self.root.after(0, self._update_description_result, description, None)

        except Exception as e:
            logging.error(f"Description generation failed: {e}")
            self.root.after(0, self._update_description_result, None, str(e))

    def _update_description_result(self, description: Optional[str], error: Optional[str]):
        """
        Update UI with description generation result.

        :param description: Generated description
        :param error: Error message if failed
        """
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate description: {error}")
            elif description and not self.ai_cancelled['description']:
                self.desc_text.delete('1.0', tk.END)
                self.desc_text.insert('1.0', description)
                self.on_description_change()
        finally:
            if not ai_coordinator.is_thread_running(self.ai_threads['description']):
                ui_components.configure_widget(self.desc_generate_button, text="Generate", state="normal")

    def generate_keywords(self):
        """Generate keywords using AI in background thread."""
        if not self.state.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return

        selected_model = self.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return

        # Check if already running
        if ai_coordinator.is_thread_running(self.ai_threads['keywords']):
            self.ai_cancelled['keywords'] = True
            ui_components.configure_widget(self.keywords_generate_button, text="Generate", state="normal")
            self.ai_threads['keywords'] = None
            return

        # Start generation
        self.ai_cancelled['keywords'] = False
        ui_components.configure_widget(self.keywords_generate_button, text="Cancel")

        self.ai_threads['keywords'] = ai_coordinator.start_generation_thread(
            self._generate_keywords_worker,
            (selected_model,)
        )

    def _generate_keywords_worker(self, selected_model: str):
        """
        Worker thread for keywords generation.

        :param selected_model: Selected model display name
        """
        try:
            available_models = ai_coordinator.load_available_models()
            model_key = ai_coordinator.find_model_by_display_name(selected_model, available_models)

            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")

            if self.ai_cancelled['keywords']:
                self.root.after(0, self._update_keywords_result, None, None)
                return

            existing_title = self.title_entry.get().strip()
            existing_desc = self.desc_text.get('1.0', tk.END).strip()
            current_keywords = self.keywords_tag_entry.get_tags()

            keyword_count = min(50, 50 - len(current_keywords))

            keywords = ai_coordinator.generate_keywords_sync(
                self.state.current_file_path,
                model_key,
                keyword_count,
                existing_title if existing_title else None,
                existing_desc if existing_desc else None,
                self.editorial_var.get()
            )

            if self.ai_cancelled['keywords']:
                self.root.after(0, self._update_keywords_result, None, None)
                return

            self.root.after(0, self._update_keywords_result, keywords, None)

        except Exception as e:
            logging.error(f"Keywords generation failed: {e}")
            self.root.after(0, self._update_keywords_result, None, str(e))

    def _update_keywords_result(self, keywords: Optional[List[str]], error: Optional[str]):
        """
        Update UI with keywords generation result.

        :param keywords: Generated keywords
        :param error: Error message if failed
        """
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate keywords: {error}")
            elif keywords and not self.ai_cancelled['keywords']:
                current_keywords = self.keywords_tag_entry.get_tags()
                for keyword in keywords:
                    if keyword not in current_keywords and len(current_keywords) < 50:
                        current_keywords.append(keyword)
                self.keywords_tag_entry.set_tags(current_keywords)
                self.on_keywords_change()
        finally:
            if not ai_coordinator.is_thread_running(self.ai_threads['keywords']):
                ui_components.configure_widget(self.keywords_generate_button, text="Generate", state="normal")

    def generate_categories(self):
        """Generate categories using AI in background thread."""
        if not self.state.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return

        selected_model = self.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return

        if not hasattr(self, 'category_combos') or not self.category_combos:
            messagebox.showinfo("No Categories", "No category dropdowns available to populate")
            return

        # Check if already running
        if ai_coordinator.is_thread_running(self.ai_threads['categories']):
            self.ai_cancelled['categories'] = True
            ui_components.configure_widget(self.categories_generate_button, text="Generate", state="normal")
            self.ai_threads['categories'] = None
            return

        # Start generation
        self.ai_cancelled['categories'] = False
        ui_components.configure_widget(self.categories_generate_button, text="Cancel")

        self.ai_threads['categories'] = ai_coordinator.start_generation_thread(
            self._generate_categories_worker,
            (selected_model,)
        )

    def _generate_categories_worker(self, selected_model: str):
        """
        Worker thread for categories generation.

        :param selected_model: Selected model display name
        """
        try:
            available_models = ai_coordinator.load_available_models()
            model_key = ai_coordinator.find_model_by_display_name(selected_model, available_models)

            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")

            if self.ai_cancelled['categories']:
                self.root.after(0, self._update_categories_result, None, None)
                return

            existing_title = self.title_entry.get().strip()
            existing_desc = self.desc_text.get('1.0', tk.END).strip()

            generated_categories = ai_coordinator.generate_categories_sync(
                self.state.current_file_path,
                model_key,
                self.categories,
                existing_title if existing_title else None,
                existing_desc if existing_desc else None
            )

            if self.ai_cancelled['categories']:
                self.root.after(0, self._update_categories_result, None, None)
                return

            self.root.after(0, self._update_categories_result, generated_categories, None)

        except Exception as e:
            logging.error(f"Categories generation failed: {e}")
            self.root.after(0, self._update_categories_result, None, str(e))

    def _update_categories_result(self, generated_categories: Optional[Dict], error: Optional[str]):
        """
        Update UI with categories generation result.

        :param generated_categories: Generated categories
        :param error: Error message if failed
        """
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate categories: {error}")
            elif generated_categories and not self.ai_cancelled['categories']:
                categories_manager.set_generated_categories(self.category_combos, generated_categories)
        finally:
            if not ai_coordinator.is_thread_running(self.ai_threads['categories']):
                ui_components.configure_widget(self.categories_generate_button, text="Generate", state="normal")

    def generate_all_metadata(self):
        """Generate all metadata serially with proper dependencies."""
        if not self.state.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return

        selected_model = self.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return

        # Check if already active
        if self._generate_all_active:
            self._cancel_all_generation()
            return

        # Start serial generation
        self._generate_all_active = True
        ui_components.configure_widget(self.generate_all_button, text="Cancel", state="normal")

        self.ai_threads['all'] = ai_coordinator.start_generation_thread(
            self._generate_all_worker,
            (selected_model,)
        )

    def _generate_all_worker(self, selected_model: str):
        """
        Worker thread that runs all generations serially.

        :param selected_model: Selected model display name
        """
        try:
            # Reset cancellation flags
            for gen_type in ['title', 'description', 'keywords', 'categories']:
                self.ai_cancelled[gen_type] = False

            # Generate title
            self._start_and_wait_for_generation('title', selected_model)
            if not self._generate_all_active or self.ai_cancelled['title']:
                return

            # Generate description
            self._start_and_wait_for_generation('description', selected_model)
            if not self._generate_all_active or self.ai_cancelled['description']:
                return

            # Generate keywords
            self._start_and_wait_for_generation('keywords', selected_model)
            if not self._generate_all_active or self.ai_cancelled['keywords']:
                return

            # Generate categories
            self._start_and_wait_for_generation('categories', selected_model)
            if not self._generate_all_active or self.ai_cancelled['categories']:
                return

            # All completed
            self.root.after(0, self._complete_all_generation)

        except Exception as e:
            logging.error(f"Generate All failed: {e}")
            self.root.after(0, self._complete_all_generation)

    def _start_and_wait_for_generation(self, gen_type: str, selected_model: str):
        """
        Start a generation and wait for it to complete.

        :param gen_type: Type of generation ('title', 'description', 'keywords', 'categories')
        :param selected_model: Selected model display name
        """
        # Update button to Cancel
        if gen_type == 'title':
            self.root.after(0, lambda: ui_components.configure_widget(self.title_generate_button, text="Cancel"))
            self.ai_threads['title'] = ai_coordinator.start_generation_thread(
                self._generate_title_worker,
                (selected_model,)
            )
            ai_coordinator.wait_for_thread(self.ai_threads['title'])
        elif gen_type == 'description':
            self.root.after(0, lambda: ui_components.configure_widget(self.desc_generate_button, text="Cancel"))
            self.ai_threads['description'] = ai_coordinator.start_generation_thread(
                self._generate_description_worker,
                (selected_model,)
            )
            ai_coordinator.wait_for_thread(self.ai_threads['description'])
        elif gen_type == 'keywords':
            self.root.after(0, lambda: ui_components.configure_widget(self.keywords_generate_button, text="Cancel"))
            self.ai_threads['keywords'] = ai_coordinator.start_generation_thread(
                self._generate_keywords_worker,
                (selected_model,)
            )
            ai_coordinator.wait_for_thread(self.ai_threads['keywords'])
        elif gen_type == 'categories':
            self.root.after(0, lambda: ui_components.configure_widget(self.categories_generate_button, text="Cancel"))
            self.ai_threads['categories'] = ai_coordinator.start_generation_thread(
                self._generate_categories_worker,
                (selected_model,)
            )
            ai_coordinator.wait_for_thread(self.ai_threads['categories'])

    def _cancel_all_generation(self):
        """Cancel all running generations and reset all buttons."""
        # Set cancellation flags
        for gen_type in ['title', 'description', 'keywords', 'categories']:
            self.ai_cancelled[gen_type] = True

        # Reset buttons
        ui_components.configure_widget(self.title_generate_button, text="Generate", state="normal")
        ui_components.configure_widget(self.desc_generate_button, text="Generate", state="normal")
        ui_components.configure_widget(self.keywords_generate_button, text="Generate", state="normal")
        ui_components.configure_widget(self.categories_generate_button, text="Generate", state="normal")

        # Reset Generate All
        self._generate_all_active = False
        ui_components.configure_widget(self.generate_all_button, text="Generate All", state="normal")

        logging.debug("All generations cancelled")

    def _complete_all_generation(self):
        """Complete the generate all process."""
        self._generate_all_active = False
        ui_components.configure_widget(self.generate_all_button, text="Generate All", state="normal")
        logging.debug("All metadata generation completed")

    def save_metadata(self):
        """Save metadata and close window."""
        if not self.state.current_record:
            messagebox.showwarning("No File", "No file is currently loaded.")
            return

        # Collect metadata
        title = self.title_entry.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        keywords = self.keywords_tag_entry.get_tags()

        # Validate
        validation = metadata_validator.validate_all_metadata(title, description, keywords)
        if not validation.is_valid:
            messagebox.showwarning("Validation Error", validation.error_message)
            return

        # Collect categories
        selected_categories = {}
        if hasattr(self, 'category_combos'):
            selected_categories = categories_manager.collect_selected_categories(self.category_combos)

        # Create metadata dict
        metadata = viewer_state.create_metadata_dict(
            viewer_state.update_state_from_ui(
                self.state,
                viewer_state.UIReferences(
                    title_entry=self.title_entry,
                    desc_text=self.desc_text,
                    keywords_tag_entry=self.keywords_tag_entry,
                    editorial_var=self.editorial_var,
                    model_combo=self.model_combo,
                    file_path_label=self.file_path_label,
                    media_label=self.media_label,
                    controls_frame=self.controls_frame,
                    category_combos=self.category_combos
                )
            ),
            selected_categories
        )

        # Call completion callback
        if self.state.completion_callback:
            self.state.completion_callback(metadata)

        self.root.destroy()

    def reject_metadata(self):
        """Reject this file and set status to rejected for all photobanks."""
        if not self.state.current_record:
            messagebox.showwarning("No File", "No file is currently loaded.")
            return

        # Confirm
        response = messagebox.askyesno(
            "Reject File",
            f"Are you sure you want to reject this file?\n\n{self.state.current_file_path}\n\n"
            "This will set status to 'zamítnuto' for all photobanks.",
            icon='warning'
        )

        if not response:
            return

        # Create rejection metadata
        metadata = viewer_state.create_rejection_metadata()

        # Call completion callback
        if self.state.completion_callback:
            self.state.completion_callback(metadata)

        self.root.destroy()

    def _show_editorial_dialog_sync(
        self,
        missing_fields: Dict[str, bool],
        extracted_data: Dict[str, str]
    ) -> Optional[Dict[str, str]]:
        """
        Show editorial dialog synchronously from worker thread.

        :param missing_fields: Dict of field -> is_missing
        :param extracted_data: Extracted editorial data
        :return: Editorial data or None if cancelled
        """
        result_container = {'result': None}
        dialog_completed = threading.Event()

        def show_dialog_in_main_thread():
            """Show dialog in main thread and store result."""
            try:
                result_container['result'] = get_editorial_metadata(
                    self.root,
                    missing_fields,
                    extracted_data
                )
            except Exception as e:
                logging.error(f"Editorial dialog error: {e}")
                result_container['result'] = None
            finally:
                dialog_completed.set()

        # Schedule dialog in main thread
        self.root.after(0, show_dialog_in_main_thread)

        # Wait for completion
        dialog_completed.wait()

        return result_container['result']

    def open_in_explorer(self):
        """Open the current file location in Windows Explorer."""
        if not self.state.current_file_path:
            messagebox.showwarning("No File", "No file is currently loaded.")
            return

        try:
            if platform.system() == "Windows":
                normalized_path = os.path.normpath(self.state.current_file_path)
                result = subprocess.run(['explorer', '/select,', normalized_path])
                logging.debug(f"Opened file location in Explorer: {normalized_path} (exit code: {result.returncode})")
            else:
                directory = os.path.dirname(self.state.current_file_path)
                if platform.system() == "Darwin":
                    subprocess.run(['open', directory])
                else:
                    subprocess.run(['xdg-open', directory])
                logging.debug(f"Opened directory: {directory}")

        except Exception as e:
            logging.error(f"Failed to open file location: {e}")
            messagebox.showerror("Error", f"Failed to open file location:\n{str(e)}")

    def on_window_close(self):
        """Handle window close event."""
        logging.debug("Window closed by user - terminating script")
        self.root.destroy()
        sys.exit(0)


def show_media_viewer(
    file_path: str,
    record: dict,
    completion_callback: Optional[Callable] = None,
    categories: Dict[str, List[str]] = None
):
    """
    Show the media viewer for a specific file and record.

    :param file_path: Path to media file
    :param record: CSV record for file
    :param completion_callback: Callback to call when metadata is saved
    :param categories: Dict of photobank -> list of categories
    """
    root = tk.Tk()
    viewer = MediaViewer(root, "", categories)
    viewer.load_media(file_path, record, completion_callback)

    # Center window
    ui_components.center_window(root)

    root.mainloop()


if __name__ == "__main__":
    # Test the viewer
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        show_media_viewer(test_file, {})
    else:
        print("Usage: python media_viewer_refactored.py <media_file>")