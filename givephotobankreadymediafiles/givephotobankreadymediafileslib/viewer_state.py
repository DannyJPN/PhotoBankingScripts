"""
State management for MediaViewer.

Handles input state, character counters, and metadata field management.
"""

import logging
import tkinter as tk
from typing import Optional, Callable, List

from givephotobankreadymediafileslib.constants import MAX_TITLE_LENGTH, MAX_DESCRIPTION_LENGTH


class ViewerState:
    """Manages viewer state including current file, metadata inputs, and UI updates."""

    def __init__(self, root: tk.Tk):
        """
        Initialize viewer state.

        Args:
            root: Tkinter root window
        """
        self.root = root

        # Current media info
        self.current_file_path: Optional[str] = None
        self.current_record: Optional[dict] = None
        self.completion_callback: Optional[Callable] = None

        # UI widget references (set by ui_components module)
        self.title_entry: Optional[tk.Entry] = None
        self.desc_text: Optional[tk.Text] = None
        self.keywords_tag_entry = None  # TagEntry widget
        self.editorial_var: Optional[tk.BooleanVar] = None

        # Character counter labels
        self.title_char_label: Optional[tk.Label] = None
        self.desc_char_label: Optional[tk.Label] = None
        self.keywords_count_label: Optional[tk.Label] = None

        # Keywords storage for compatibility
        self.keywords_list: List[str] = []

        # Button state update callback (set by metadata_validator module)
        self.update_button_states_callback: Optional[Callable] = None

    def on_title_change(self, event=None):
        """
        Update title character counter and enforce character limit.

        Enhanced to enforce MAX_TITLE_LENGTH by truncating input.
        """
        if not self.title_entry or not self.title_char_label:
            return

        current_text = self.title_entry.get()
        current_length = len(current_text)

        # Enforce character limit by truncating
        if current_length > MAX_TITLE_LENGTH:
            truncated_text = current_text[:MAX_TITLE_LENGTH]
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, truncated_text)
            current_length = MAX_TITLE_LENGTH

        self.title_char_label.configure(text=f"{current_length}/{MAX_TITLE_LENGTH}")
        if current_length == MAX_TITLE_LENGTH:
            self.title_char_label.configure(foreground='red')
        else:
            self.title_char_label.configure(foreground='black')
        # Note: Button state update happens on focus loss, not on keystroke

    def on_title_focus_out(self, event=None) -> None:
        """
        Handle title field losing focus - update button states with debouncing.

        NEW ENHANCEMENT: Triggers debounced button state update when user leaves title field.
        """
        if self.update_button_states_callback:
            self.update_button_states_callback()

    def on_description_change(self, event=None):
        """
        Update description character counter and enforce character limit.

        Enhanced to enforce MAX_DESCRIPTION_LENGTH by truncating input.
        """
        if not self.desc_text or not self.desc_char_label:
            return

        # Get current text (tk.Text adds a newline at the end, so we strip it)
        current_text = self.desc_text.get('1.0', tk.END).rstrip('\n')
        current_length = len(current_text)

        # Enforce character limit by truncating
        if current_length > MAX_DESCRIPTION_LENGTH:
            truncated_text = current_text[:MAX_DESCRIPTION_LENGTH]
            self.desc_text.delete('1.0', tk.END)
            self.desc_text.insert('1.0', truncated_text)
            current_length = MAX_DESCRIPTION_LENGTH

        self.desc_char_label.configure(text=f"{current_length}/{MAX_DESCRIPTION_LENGTH}")
        if current_length == MAX_DESCRIPTION_LENGTH:
            self.desc_char_label.configure(foreground='red')
        else:
            self.desc_char_label.configure(foreground='black')
        # Note: Button state update happens on focus loss, not on keystroke

    def on_description_focus_out(self, event=None) -> None:
        """
        Handle description field losing focus - update button states with debouncing.

        NEW ENHANCEMENT: Triggers debounced button state update when user leaves description field.
        """
        if self.update_button_states_callback:
            self.update_button_states_callback()

    def on_keywords_change(self) -> None:
        """Handle keywords change from TagEntry widget."""
        if not self.keywords_tag_entry:
            return

        # Update keywords list for compatibility with existing code
        self.keywords_list = self.keywords_tag_entry.get_tags()
        self.update_keywords_counter()
        # Note: Button state update happens on focus loss, not on change

    def on_keywords_focus_out(self, event=None) -> None:
        """
        Handle keywords field losing focus - update button states with debouncing.

        NEW ENHANCEMENT: Triggers debounced button state update when user leaves keywords field.
        """
        if self.update_button_states_callback:
            self.update_button_states_callback()

    def refresh_keywords_display(self):
        """Refresh the keywords display after loading from file."""
        if not self.keywords_tag_entry:
            return

        # Set tags in the new TagEntry widget
        self.keywords_tag_entry.set_tags(self.keywords_list)

        # Update counter
        self.update_keywords_counter()

    def update_keywords_counter(self):
        """Update keywords counter."""
        if not self.keywords_count_label:
            return

        current_count = len(self.keywords_list)
        self.keywords_count_label.configure(text=f"{current_count}/50")
        if current_count >= 50:
            self.keywords_count_label.configure(foreground='red')
        else:
            self.keywords_count_label.configure(foreground='black')

    def handle_title_input(self, event):
        """Handle title input Enter key."""
        if self.desc_text:
            # Move focus to description
            self.desc_text.focus()

    def load_metadata_from_record(self, record: dict):
        """
        Load existing metadata from record into UI widgets.

        Args:
            record: CSV record dictionary with metadata
        """
        if not self.title_entry or not self.desc_text:
            logging.warning("Cannot load metadata - UI widgets not initialized")
            return

        # Load title
        title = record.get('Název', '')
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, title)
        self.on_title_change()  # Update character counter

        # Load description
        description = record.get('Popis', '')
        self.desc_text.delete('1.0', tk.END)
        self.desc_text.insert('1.0', description)
        self.on_description_change()  # Update character counter

        # Load keywords into tags
        keywords = record.get('Klíčová slova', '')
        self.keywords_list.clear()
        if keywords:
            for keyword in keywords.split(','):
                keyword = keyword.strip()
                if keyword:
                    self.keywords_list.append(keyword)
        self.refresh_keywords_display()

        # Load editorial mode
        editorial = record.get('Editorial', False)
        if isinstance(editorial, str):
            editorial = editorial.lower() in ('true', '1', 'yes', 'ano')
        if self.editorial_var:
            self.editorial_var.set(bool(editorial))

    def collect_metadata(self) -> dict:
        """
        Collect current metadata from UI widgets.

        Returns:
            Dictionary with title, description, keywords, editorial flag
        """
        if not self.title_entry or not self.desc_text:
            logging.warning("Cannot collect metadata - UI widgets not initialized")
            return {}

        title = self.title_entry.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        keywords = ', '.join(self.keywords_list)
        editorial = self.editorial_var.get() if self.editorial_var else False

        return {
            'title': title,
            'description': description,
            'keywords': keywords,
            'editorial': editorial
        }