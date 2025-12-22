"""
UI components module for MediaViewer.

Handles UI layout, setup, and debounced button state updates.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from givephotobankreadymediafileslib.tag_entry import TagEntry
from givephotobankreadymediafileslib.constants import MAX_TITLE_LENGTH, MAX_DESCRIPTION_LENGTH


class UIComponents:
    """Manages UI component setup and layout."""

    def __init__(self, root: tk.Tk):
        """
        Initialize UI components.

        Args:
            root: Tkinter root window
        """
        self.root = root

        # Debouncing timer for button state updates (NEW ENHANCEMENT)
        self._button_update_timer: Optional[str] = None

        # Callback for actual button state update logic (set by metadata_validator module)
        self._button_update_callback: Optional[Callable] = None

        # Widget references for other modules
        self.media_label: Optional[ttk.Label] = None
        self.controls_frame: Optional[ttk.Frame] = None
        self.play_button: Optional[ttk.Button] = None
        self.stop_button: Optional[ttk.Button] = None
        self.video_progress: Optional[ttk.Scale] = None
        self.time_label: Optional[ttk.Label] = None
        self.file_path_label: Optional[ttk.Label] = None
        self.model_combo: Optional[ttk.Combobox] = None
        self.title_entry: Optional[ttk.Entry] = None
        self.title_char_label: Optional[ttk.Label] = None
        self.title_generate_button: Optional[ttk.Button] = None
        self.desc_text: Optional[tk.Text] = None
        self.desc_char_label: Optional[ttk.Label] = None
        self.desc_generate_button: Optional[ttk.Button] = None
        self.keywords_tag_entry: Optional[TagEntry] = None
        # Note: keywords_count_label removed - TagEntry has built-in counter
        self.keywords_generate_button: Optional[ttk.Button] = None
        self.editorial_var: Optional[tk.BooleanVar] = None
        self.editorial_checkbox: Optional[ttk.Checkbutton] = None
        self.categories_container: Optional[ttk.Frame] = None
        self.categories_generate_button: Optional[ttk.Button] = None
        self.generate_all_button: Optional[ttk.Button] = None
        self.save_button: Optional[ttk.Button] = None
        self.reject_button: Optional[ttk.Button] = None
        self.explorer_button: Optional[ttk.Button] = None

    def setup_styles(self):
        """Setup custom styles for UI components."""
        style = ttk.Style()

        # Configure tag frame style
        style.configure('Tag.TFrame',
                       background='lightblue',
                       relief='raised',
                       borderwidth=1)

        # Configure reject button style (red text)
        style.configure('Reject.TButton', foreground='red')

    def setup_ui(self, media_panel_callbacks: dict, metadata_panel_callbacks: dict):
        """
        Setup the main UI layout.

        Args:
            media_panel_callbacks: Callbacks for media panel (toggle_video, stop_video, seek_video)
            metadata_panel_callbacks: Callbacks for metadata panel (event handlers, generation functions)
        """
        # Create main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel for media display
        self.setup_media_panel(main_paned, media_panel_callbacks)

        # Right panel for metadata interface
        self.setup_metadata_panel(main_paned, metadata_panel_callbacks)

    def setup_media_panel(self, parent, callbacks: dict):
        """
        Setup the left panel for media display.

        Args:
            parent: Parent widget
            callbacks: Dictionary with toggle_video, stop_video, seek_video callbacks
        """
        media_frame = ttk.Frame(parent)
        parent.add(media_frame, weight=2)

        # Media display area
        self.media_label = ttk.Label(media_frame, text="No media loaded",
                                   anchor=tk.CENTER, background='black', foreground='white')
        self.media_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Video controls frame
        controls_frame = ttk.Frame(media_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        self.play_button = ttk.Button(controls_frame, text="Play", command=callbacks.get('toggle_video'))
        self.play_button.pack(side=tk.LEFT, padx=2)

        self.stop_button = ttk.Button(controls_frame, text="Stop", command=callbacks.get('stop_video'))
        self.stop_button.pack(side=tk.LEFT, padx=2)

        # Video progress bar
        self.video_progress = ttk.Scale(controls_frame, orient=tk.HORIZONTAL,
                                      from_=0, to=100, command=callbacks.get('seek_video'))
        self.video_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Time labels
        self.time_label = ttk.Label(controls_frame, text="00:00 / 00:00")
        self.time_label.pack(side=tk.RIGHT, padx=2)

        # Initially hide video controls
        controls_frame.pack_forget()
        self.controls_frame = controls_frame

    def setup_metadata_panel(self, parent, callbacks: dict):
        """
        Setup the right panel with metadata interface - horizontal layout with vertical keywords.

        Args:
            parent: Parent widget
            callbacks: Dictionary with all event handlers and generation callbacks
        """
        control_frame = ttk.Frame(parent)
        parent.add(control_frame, weight=1)

        # Create horizontal paned window for left fields + right keywords listbox
        metadata_paned = ttk.PanedWindow(control_frame, orient=tk.HORIZONTAL)
        metadata_paned.pack(fill=tk.BOTH, expand=True, pady=(0, 0))

        # Left side - metadata fields (wider)
        left_frame = ttk.Frame(metadata_paned)
        metadata_paned.add(left_frame, weight=3)

        # Right side - keywords listbox (narrower)
        right_frame = ttk.Frame(metadata_paned)
        metadata_paned.add(right_frame, weight=2)

        # File path display (in left frame)
        path_frame = ttk.LabelFrame(left_frame, text="Current File")
        path_frame.pack(fill=tk.X, padx=5, pady=(5, 2))

        self.file_path_label = ttk.Label(path_frame, text="No file loaded",
                                       wraplength=250, justify=tk.LEFT)
        self.file_path_label.pack(padx=10, pady=5, anchor=tk.W)

        # AI Model Selection (in left frame)
        self.setup_ai_model_panel(left_frame, callbacks.get('on_model_selected'))

        # Title input (in left frame, narrower)
        title_frame = ttk.LabelFrame(left_frame, text="Title")
        title_frame.pack(fill=tk.X, padx=5, pady=(2, 2))

        ttk.Label(title_frame, text="Enter title:").pack(anchor=tk.W, padx=10, pady=(5, 3))

        # Title entry (smaller width)
        self.title_entry = ttk.Entry(title_frame, width=30)
        self.title_entry.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.title_entry.bind('<KeyRelease>', callbacks.get('on_title_change'))
        self.title_entry.bind('<Return>', callbacks.get('handle_title_input'))
        self.title_entry.bind('<FocusOut>', callbacks.get('on_title_focus_out'))  # NEW ENHANCEMENT

        # Title controls
        title_controls_frame = ttk.Frame(title_frame)
        title_controls_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.title_char_label = ttk.Label(title_controls_frame, text=f"0/{MAX_TITLE_LENGTH}")
        self.title_char_label.pack(side=tk.LEFT)

        self.title_generate_button = ttk.Button(title_controls_frame, text="Generate",
                                               command=callbacks.get('generate_title'))
        self.title_generate_button.pack(side=tk.RIGHT)

        # Description input (in left frame, taller)
        desc_frame = ttk.LabelFrame(left_frame, text="Description")
        desc_frame.pack(fill=tk.X, padx=5, pady=(2, 2))

        ttk.Label(desc_frame, text="Enter description:").pack(anchor=tk.W, padx=10, pady=(5, 3))

        # Description text (taller for 200+ chars)
        self.desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD, font=('Arial', 9), width=30)
        self.desc_text.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.desc_text.bind('<KeyRelease>', callbacks.get('on_description_change'))
        self.desc_text.bind('<FocusOut>', callbacks.get('on_description_focus_out'))  # NEW ENHANCEMENT

        # Description controls
        desc_controls_frame = ttk.Frame(desc_frame)
        desc_controls_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.desc_char_label = ttk.Label(desc_controls_frame, text=f"0/{MAX_DESCRIPTION_LENGTH}")
        self.desc_char_label.pack(side=tk.LEFT)

        self.desc_generate_button = ttk.Button(desc_controls_frame, text="Generate",
                                              command=callbacks.get('generate_description'))
        self.desc_generate_button.pack(side=tk.RIGHT)

        # Keywords - vertical listbox (in right frame, fixed height, ends above categories)
        keywords_frame = ttk.LabelFrame(right_frame, text="Keywords (Tags)")
        keywords_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))

        # TagEntry widget - narrower width, expands to fill available height
        self.keywords_tag_entry = TagEntry(keywords_frame, width=25,
                                          max_tags=50, on_change=callbacks.get('on_keywords_change'))
        self.keywords_tag_entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 5))
        # Bind focus out to update button states (NEW ENHANCEMENT)
        self.keywords_tag_entry.bind('<FocusOut>', callbacks.get('on_keywords_focus_out'))

        # Keywords controls at bottom
        keywords_controls_frame = ttk.Frame(keywords_frame)
        keywords_controls_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Note: TagEntry widget has built-in counter, no need for external label

        self.keywords_generate_button = ttk.Button(keywords_controls_frame, text="Generate",
                                                  command=callbacks.get('generate_keywords'))
        self.keywords_generate_button.pack(side=tk.RIGHT)

        # Editorial checkbox (in left frame)
        editorial_frame = ttk.LabelFrame(left_frame, text="Editorial Mode")
        editorial_frame.pack(fill=tk.X, padx=5, pady=(2, 0))

        self.editorial_var = tk.BooleanVar()
        self.editorial_checkbox = ttk.Checkbutton(editorial_frame, text="Editorial mode",
                                                 variable=self.editorial_var)
        self.editorial_checkbox.pack(anchor=tk.W, padx=10, pady=5)

        # Categories selection spanning full width (below horizontal paned window)
        self.setup_categories_panel(control_frame, callbacks.get('generate_categories'))

        # Action buttons (span full width at bottom)
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=10, side=tk.BOTTOM)

        self.generate_all_button = ttk.Button(action_frame, text="Generate All",
                                            command=callbacks.get('generate_all_metadata'))
        self.generate_all_button.pack(side=tk.LEFT, padx=2)

        self.save_button = ttk.Button(action_frame, text="Save & Continue",
                                    command=callbacks.get('save_metadata'))
        self.save_button.pack(side=tk.LEFT, padx=2)

        self.reject_button = ttk.Button(action_frame, text="Reject",
                                      command=callbacks.get('reject_metadata'),
                                      style='Reject.TButton')
        self.reject_button.pack(side=tk.LEFT, padx=2)

        self.explorer_button = ttk.Button(action_frame, text="Open in Explorer",
                                        command=callbacks.get('open_in_explorer'))
        self.explorer_button.pack(side=tk.LEFT, padx=2)

    def setup_ai_model_panel(self, parent, on_model_selected_callback):
        """
        Setup AI model selection panel - simple dropdown only.

        Args:
            parent: Parent widget
            on_model_selected_callback: Callback for model selection change
        """
        model_frame = ttk.LabelFrame(parent, text="AI Model Selection")
        model_frame.pack(fill=tk.X, padx=5, pady=(2, 2))

        # Model selection dropdown - compact layout
        selection_frame = ttk.Frame(model_frame)
        selection_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(selection_frame, text="Model:").pack(side=tk.LEFT, padx=(0, 5))

        self.model_combo = ttk.Combobox(selection_frame, state="readonly", width=30)
        self.model_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Bind selection change
        if on_model_selected_callback:
            self.model_combo.bind('<<ComboboxSelected>>', on_model_selected_callback)

    def setup_categories_panel(self, parent, generate_categories_callback):
        """
        Setup categories selection panel with all photobanks.

        Args:
            parent: Parent widget
            generate_categories_callback: Callback for category generation
        """
        categories_frame = ttk.LabelFrame(parent, text="Categories")
        categories_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        # Categories selection with generate button
        categories_input_frame = ttk.Frame(categories_frame)
        categories_input_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(categories_input_frame, text="Select categories:").pack(side=tk.LEFT, padx=(0, 5))

        self.categories_generate_button = ttk.Button(categories_input_frame, text="Generate",
                                                    command=generate_categories_callback)
        self.categories_generate_button.pack(side=tk.RIGHT)

        # Direct frame for categories (no scrolling needed)
        self.categories_container = ttk.Frame(categories_frame)
        self.categories_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def update_all_button_states_debounced(self, delay_ms: int = 200) -> None:
        """
        Debounced version of update_all_button_states() for text input handlers.

        NEW ENHANCEMENT: This prevents excessive button state updates during rapid typing by delaying
        the update until the user stops typing for delay_ms milliseconds.

        Args:
            delay_ms: Delay in milliseconds before updating (default: 200ms)
        """
        # Cancel any pending update
        if self._button_update_timer:
            self.root.after_cancel(self._button_update_timer)

        # Schedule new update
        if self._button_update_callback:
            self._button_update_timer = self.root.after(delay_ms, self._button_update_callback)

    def set_button_update_callback(self, callback: Callable):
        """
        Set callback for button state updates.

        Args:
            callback: Function to call when button states need to be updated
        """
        self._button_update_callback = callback