"""
Metadata validation and button state management module for MediaViewer.

NEW ENHANCEMENT: Implements intelligent button state management based on available inputs
and model capabilities, with provider caching optimization.
"""

import os
import logging
from typing import Dict, Optional
from tkinter import ttk


class MetadataValidator:
    """Manages metadata validation and button state logic."""

    def __init__(self, viewer_state, ui_components, ai_coordinator, categories_manager):
        """
        Initialize metadata validator.

        Args:
            viewer_state: ViewerState instance
            ui_components: UIComponents instance
            ai_coordinator: AICoordinator instance
            categories_manager: CategoriesManager instance
        """
        self.viewer_state = viewer_state
        self.ui_components = ui_components
        self.ai_coordinator = ai_coordinator
        self.categories_manager = categories_manager

    def check_available_inputs(self, field_type: str) -> Dict[str, bool]:
        """
        Check what inputs are available for the given field generation.

        NEW ENHANCEMENT: Determines whether image and/or text inputs are available for each field type.

        Args:
            field_type: One of 'title', 'description', 'keywords', 'categories'

        Returns:
            Dict with 'has_image', 'has_text' keys
        """
        has_image = (self.viewer_state.current_file_path is not None and
                    os.path.exists(self.viewer_state.current_file_path))

        # Check what text inputs are available
        has_text = False

        if field_type == 'title':
            # Title generation doesn't need existing text (can generate from scratch)
            # But if there's existing title, it could be used for refinement
            existing_title = self.viewer_state.title_entry.get().strip()
            has_text = len(existing_title) > 0

        elif field_type == 'description':
            # Description can use existing title or existing description
            existing_title = self.viewer_state.title_entry.get().strip()
            existing_desc = self.viewer_state.desc_text.get('1.0', 'end').strip()
            has_text = len(existing_title) > 0 or len(existing_desc) > 0

        elif field_type == 'keywords':
            # Keywords can use title, description, or existing keywords
            existing_title = self.viewer_state.title_entry.get().strip()
            existing_desc = self.viewer_state.desc_text.get('1.0', 'end').strip()
            existing_keywords = self.viewer_state.keywords_list
            has_text = len(existing_title) > 0 or len(existing_desc) > 0 or len(existing_keywords) > 0

        elif field_type == 'categories':
            # Categories can use title and description
            existing_title = self.viewer_state.title_entry.get().strip()
            existing_desc = self.viewer_state.desc_text.get('1.0', 'end').strip()
            has_text = len(existing_title) > 0 or len(existing_desc) > 0

        return {
            'has_image': has_image,
            'has_text': has_text
        }

    def should_enable_generation_button(self, field_type: str, ai_provider: Optional['AIProvider'] = None) -> bool:
        """
        Determine if a generation button should be enabled.

        NEW ENHANCEMENT: Intelligent button state logic based on available inputs and model capabilities.
        Supports provider caching optimization - pass ai_provider to avoid repeated lookups.

        Args:
            field_type: One of 'title', 'description', 'keywords', 'categories'
            ai_provider: Optional AI provider instance (if None, will be fetched)

        Returns:
            True if button should be enabled
        """
        # Always disable if no file is loaded
        if not self.viewer_state.current_file_path:
            logging.debug(f"Button {field_type}: Disabled - no file loaded")
            return False

        # Check available inputs
        inputs = self.check_available_inputs(field_type)

        # Log only in debug mode to reduce spam
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(f"Button {field_type}: has_image={inputs['has_image']}, has_text={inputs['has_text']}")

        # If we have no inputs at all, disable
        if not inputs['has_image'] and not inputs['has_text']:
            logging.debug(f"Button {field_type}: Disabled - no inputs available")
            return False

        # Get AI provider if not provided (OPTIMIZATION: reuse provider across multiple checks)
        if ai_provider is None:
            ai_provider = self.ai_coordinator.get_current_ai_provider()

        if not ai_provider:
            # Cannot determine model capabilities - disable button to prevent errors
            # Distinguish between initialization (expected) and runtime error (unexpected)
            from shared.config import get_config
            config = get_config()
            has_default = bool(config.get_default_ai_model())

            if has_default and not self.ui_components.model_combo.get():
                # Initialization phase - default model not loaded yet
                logging.debug(f"Button {field_type}: Disabled - AI provider unavailable (initialization in progress)")
            else:
                # Runtime error - model should be available but isn't
                logging.warning(f"Button {field_type}: Disabled - AI provider unavailable (check model selection)")
            return False

        # Check if model can generate with available inputs
        can_generate = ai_provider.can_generate_with_inputs(
            has_image=inputs['has_image'],
            has_text=inputs['has_text']
        )

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(f"Button {field_type}: {'Enabled' if can_generate else 'Disabled'} - can_generate={can_generate}")

        return can_generate

    def update_all_button_states(self) -> None:
        """
        Update enabled/disabled state of all generation buttons.

        NEW ENHANCEMENT: Centralizes button state updates with provider caching optimization.
        """
        if not hasattr(self.ui_components, 'title_generate_button'):
            # UI not fully initialized yet
            return

        # Get AI provider once and reuse for all buttons (PERFORMANCE OPTIMIZATION)
        ai_provider = self.ai_coordinator.get_current_ai_provider()

        # Update individual generation buttons
        self.update_button_state('title', self.ui_components.title_generate_button, ai_provider)
        self.update_button_state('description', self.ui_components.desc_generate_button, ai_provider)
        self.update_button_state('keywords', self.ui_components.keywords_generate_button, ai_provider)
        self.update_button_state('categories', self.ui_components.categories_generate_button, ai_provider)

        # Update Generate All button - enabled if ANY individual button is enabled
        any_enabled = (
            str(self.ui_components.title_generate_button['state']) == 'normal' or
            str(self.ui_components.desc_generate_button['state']) == 'normal' or
            str(self.ui_components.keywords_generate_button['state']) == 'normal' or
            str(self.ui_components.categories_generate_button['state']) == 'normal'
        )
        self.ui_components.generate_all_button.configure(state='normal' if any_enabled else 'disabled')

    def update_button_state(self, field_type: str, button: ttk.Button, ai_provider: Optional['AIProvider'] = None) -> None:
        """
        Update a single button's state.

        Args:
            field_type: Type of field
            button: Button widget to update
            ai_provider: Optional AI provider instance (performance optimization)
        """
        # Don't update button state if generation is currently running for this field
        # Use thread-safe check instead of reading button text (prevents race condition)
        with self.ai_coordinator.generation_lock:
            if field_type in self.ai_coordinator.ai_threads:
                thread = self.ai_coordinator.ai_threads[field_type]
                thread_alive = thread and thread.is_alive()

        if thread_alive:
            return

        should_enable = self.should_enable_generation_button(field_type, ai_provider)
        button.configure(state='normal' if should_enable else 'disabled')