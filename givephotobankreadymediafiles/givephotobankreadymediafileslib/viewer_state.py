"""
State management for media viewer.

This module handles:
- Media viewer state dataclasses
- State initialization and updates
- State persistence helpers
"""

from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field
from PIL import ImageTk


@dataclass
class MediaViewerState:
    """
    Current state of the media viewer.

    :param current_file_path: Path to currently loaded file
    :param current_record: CSV record for current file
    :param current_image: Current PhotoImage (must be stored to prevent GC)
    :param original_image_size: Original image size (width, height)
    :param video_playing: Whether video is currently playing
    :param video_paused: Whether video is paused
    :param completion_callback: Callback to call when metadata is saved
    :param title: Current title text
    :param description: Current description text
    :param keywords: Current list of keywords
    :param editorial: Whether editorial mode is enabled
    :param selected_model: Selected AI model display name
    """

    current_file_path: Optional[str] = None
    current_record: Optional[dict] = None
    current_image: Optional[ImageTk.PhotoImage] = None
    original_image_size: Optional[tuple] = None
    video_playing: bool = False
    video_paused: bool = False
    completion_callback: Optional[Callable] = None
    title: str = ""
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    editorial: bool = False
    selected_model: str = ""


@dataclass
class UIReferences:
    """
    References to UI widgets for state updates.

    :param title_entry: Title entry widget
    :param desc_text: Description text widget
    :param keywords_tag_entry: Keywords tag entry widget
    :param editorial_var: Editorial checkbox variable
    :param model_combo: Model selection combobox
    :param file_path_label: File path label widget
    :param media_label: Media display label widget
    :param controls_frame: Video controls frame widget
    :param category_combos: Dict of photobank -> list of category comboboxes
    """

    title_entry: object  # ttk.Entry
    desc_text: object  # tk.Text
    keywords_tag_entry: object  # TagEntry
    editorial_var: object  # tk.BooleanVar
    model_combo: object  # ttk.Combobox
    file_path_label: object  # ttk.Label
    media_label: object  # ttk.Label
    controls_frame: object  # ttk.Frame
    category_combos: Dict[str, List[object]] = field(default_factory=dict)


def create_initial_state() -> MediaViewerState:
    """
    Create initial media viewer state.

    :return: MediaViewerState with default values
    """
    return MediaViewerState()


def update_state_from_ui(state: MediaViewerState, ui_refs: UIReferences) -> MediaViewerState:
    """
    Update state from current UI values.

    :param state: Current state to update
    :param ui_refs: UI widget references
    :return: Updated state
    """
    import tkinter as tk

    # Update title
    state.title = ui_refs.title_entry.get().strip()

    # Update description
    state.description = ui_refs.desc_text.get('1.0', tk.END).strip()

    # Update keywords
    state.keywords = ui_refs.keywords_tag_entry.get_tags()

    # Update editorial
    state.editorial = ui_refs.editorial_var.get()

    # Update selected model
    state.selected_model = ui_refs.model_combo.get()

    return state


def load_state_from_record(state: MediaViewerState, record: dict) -> MediaViewerState:
    """
    Load state from CSV record.

    :param state: State to update
    :param record: CSV record dict
    :return: Updated state
    """
    # Load metadata from record
    state.title = record.get('Název', '')
    state.description = record.get('Popis', '')

    # Load keywords
    keywords_str = record.get('Klíčová slova', '')
    state.keywords.clear()
    if keywords_str:
        for keyword in keywords_str.split(','):
            keyword = keyword.strip()
            if keyword:
                state.keywords.append(keyword)

    # Load editorial mode
    editorial = record.get('Editorial', False)
    if isinstance(editorial, str):
        editorial = editorial.lower() in ('true', '1', 'yes', 'ano')
    state.editorial = bool(editorial)

    return state


def sync_ui_from_state(state: MediaViewerState, ui_refs: UIReferences) -> None:
    """
    Synchronize UI widgets from state.

    :param state: Current state
    :param ui_refs: UI widget references
    """
    import tkinter as tk

    # Update title entry
    ui_refs.title_entry.delete(0, tk.END)
    ui_refs.title_entry.insert(0, state.title)

    # Update description text
    ui_refs.desc_text.delete('1.0', tk.END)
    ui_refs.desc_text.insert('1.0', state.description)

    # Update keywords
    ui_refs.keywords_tag_entry.set_tags(state.keywords)

    # Update editorial checkbox
    ui_refs.editorial_var.set(state.editorial)

    # Update file path label
    if state.current_file_path:
        ui_refs.file_path_label.configure(text=state.current_file_path)


def create_metadata_dict(state: MediaViewerState, selected_categories: Dict[str, List[str]]) -> dict:
    """
    Create metadata dictionary from current state.

    :param state: Current state
    :param selected_categories: Selected categories per photobank
    :return: Metadata dictionary
    """
    return {
        'title': state.title,
        'description': state.description,
        'keywords': ', '.join(state.keywords),
        'editorial': state.editorial,
        'categories': selected_categories,
        'ai_model': state.selected_model
    }


def create_rejection_metadata() -> dict:
    """
    Create metadata dictionary for file rejection.

    :return: Rejection metadata dictionary
    """
    return {
        'title': '',
        'description': '',
        'keywords': '',
        'editorial': False,
        'categories': {},
        'rejected': True
    }