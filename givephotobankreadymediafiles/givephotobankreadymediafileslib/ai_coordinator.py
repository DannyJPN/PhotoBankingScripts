"""
AI coordination module for MediaViewer.

Handles AI model selection, metadata generation, and threading.
"""

import logging
import traceback
import threading
from typing import Optional, List, Dict
from tkinter import messagebox

from givephotobankreadymediafileslib.editorial_dialog import (
    get_editorial_metadata, extract_editorial_metadata_from_exif
)


class AICoordinator:
    """Manages AI model selection and metadata generation in background threads."""

    def __init__(self, root, viewer_state, categories_manager, ui_components):
        """
        Initialize AI coordinator.

        Args:
            root: Tkinter root window
            viewer_state: ViewerState instance
            categories_manager: CategoriesManager instance
            ui_components: UIComponents instance
        """
        self.root = root
        self.viewer_state = viewer_state
        self.categories_manager = categories_manager
        self.ui_components = ui_components

        # AI generation state - separate threads for each type
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

        # Thread generation IDs - prevent stale threads from updating UI
        self.generation_counter = {
            'title': 0,
            'description': 0,
            'keywords': 0,
            'categories': 0
        }
        self.current_generation_id = {
            'title': 0,
            'description': 0,
            'keywords': 0,
            'categories': 0
        }

        self.generation_lock = threading.Lock()

        # Generate All state
        self._generate_all_active = False

        # Photobank categories (set externally)
        self.photobank_categories: Dict[str, List[str]] = {}

    def load_ai_models(self):
        """Load available AI models from configuration - lazy loading."""
        try:
            # Load config only when needed
            from shared.config import get_config
            config = get_config()

            available_models = config.get_available_ai_models()

            if not available_models:
                logging.warning("No AI models available - check API keys in environment or config")
                self.ui_components.model_combo.configure(values=["No models available"])
                self.ui_components.model_combo.set("No models available")
                return

            # Populate combo box
            model_names = [model["display_name"] for model in available_models]
            self.ui_components.model_combo.configure(values=model_names)

            # Set default model
            default_provider, default_model = config.get_default_ai_model()
            default_key = f"{default_provider}/{default_model}"

            for i, model in enumerate(available_models):
                if model["key"] == default_key:
                    self.ui_components.model_combo.current(i)
                    break
            else:
                # Default not found, select first
                if available_models:
                    self.ui_components.model_combo.current(0)

            # Update button states after model is loaded
            if hasattr(self, 'update_all_button_states_callback') and self.update_all_button_states_callback:
                self.update_all_button_states_callback()

        except Exception as e:
            logging.error(f"Error loading AI models: {e}")
            self.ui_components.model_combo.configure(values=["Error loading models"])
            self.ui_components.model_combo.set("Error loading models")

    def get_current_ai_provider(self):
        """
        Get the current AI provider instance based on selected model.

        NEW ENHANCEMENT: Optimized for performance - used as cache parameter in button state updates.

        Returns:
            AI provider instance or None
        """
        try:
            selected_model = self.ui_components.model_combo.get()
            if not selected_model or selected_model in ["No models available", "Error loading models"]:
                logging.debug(f"get_current_ai_provider: No valid model selected: '{selected_model}'")
                return None

            from shared.config import get_config
            from shared.ai_factory import create_from_model_key

            config = get_config()
            available_models = config.get_available_ai_models()

            # Find model key
            model_key = None
            for model in available_models:
                if model["display_name"] == selected_model:
                    model_key = model["key"]
                    break

            if not model_key:
                logging.debug(f"get_current_ai_provider: Model key not found for '{selected_model}'")
                return None

            # Create provider from model key
            provider = create_from_model_key(model_key)
            logging.debug(f"get_current_ai_provider: Got provider for '{selected_model}' (key: {model_key})")
            return provider

        except Exception as e:
            logging.error(f"Error getting AI provider: {e}")
            logging.debug(traceback.format_exc())
            return None

    def generate_title(self):
        """Generate title using AI in background thread."""
        if not self.viewer_state.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return

        selected_model = self.ui_components.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return

        # Check if title generation is already running
        if self.ai_threads['title'] and self.ai_threads['title'].is_alive():
            # Cancel current generation
            with self.generation_lock:
                self.ai_cancelled['title'] = True
                # If Generate All is active, cancel it too
                if self._generate_all_active:
                    self._generate_all_active = False
                    logging.debug("Individual title cancellation triggered Generate All cancellation")
                    # Let finally blocks handle cleanup when Generate All is active
                    return

            # Not under Generate All - reset immediately
            self.ui_components.title_generate_button.configure(text="Generate", state="normal")
            self.ai_threads['title'] = None
            return

        # Start generation in background thread with unique generation ID
        with self.generation_lock:
            self.ai_cancelled['title'] = False
            self.generation_counter['title'] += 1
            generation_id = self.generation_counter['title']
            self.current_generation_id['title'] = generation_id

        self.ai_threads['title'] = threading.Thread(
            target=self._generate_title_worker,
            args=(selected_model, generation_id),
            daemon=True
        )
        self.ui_components.title_generate_button.configure(text="Cancel")
        self.ai_threads['title'].start()
        logging.debug(f"Started title generation with ID {generation_id}")

    def _generate_title_worker(self, selected_model: str, generation_id: int):
        """Worker thread for title generation."""
        try:
            # Get AI provider from config
            from shared.config import get_config
            from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator

            config = get_config()
            available_models = config.get_available_ai_models()

            # Find model key
            model_key = None
            for model in available_models:
                if model["display_name"] == selected_model:
                    model_key = model["key"]
                    break

            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")

            # Check for cancellation
            with self.generation_lock:
                cancelled = self.ai_cancelled['title']
            if cancelled:
                self.root.after(0, self._update_title_result, None, None, generation_id)
                return

            # Create generator and generate title (returns str for original only)
            generator = create_metadata_generator(model_key)
            existing_title = self.viewer_state.title_entry.get().strip()
            title = generator.generate_title(self.viewer_state.current_file_path,
                                            existing_title if existing_title else None)

            # Check for cancellation before updating UI
            with self.generation_lock:
                cancelled = self.ai_cancelled['title']
            if cancelled:
                self.root.after(0, self._update_title_result, None, None, generation_id)
                return

            # Update UI in main thread with generated title
            self.root.after(0, self._update_title_result, title, None, generation_id)

        except Exception as e:
            logging.error(f"Title generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_title_result, None, str(e), generation_id)

    def _update_title_result(self, title: Optional[str], error: Optional[str], generation_id: int):
        """Update UI with title generation result (called in main thread)."""
        try:
            # Check if this result is from the current generation
            with self.generation_lock:
                is_current = (generation_id == self.current_generation_id['title'])
                cancelled = self.ai_cancelled['title']

            if not is_current:
                logging.debug(f"Title generation {generation_id} is stale (current: {self.current_generation_id['title']}) - ignoring result")
                return

            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate title: {error}")
            else:
                if title and not cancelled:
                    self.viewer_state.title_entry.delete(0, 'end')
                    self.viewer_state.title_entry.insert(0, title)
                    self.viewer_state.on_title_change()
                    logging.debug(f"Title generation {generation_id} completed successfully")
        finally:
            # Reset button only if no new thread is running AND not running under Generate All
            with self.generation_lock:
                is_generate_all_active = self._generate_all_active
                is_current = (generation_id == self.current_generation_id['title'])

            # Only reset button if this is still the current generation
            if is_current and not (self.ai_threads['title'] and self.ai_threads['title'].is_alive()):
                # If Generate All is NOT active, reset button to normal state
                # If Generate All IS active, button will be reset by Generate All completion
                if not is_generate_all_active:
                    self.ui_components.title_generate_button.configure(text="Generate", state="normal")

    def generate_description(self):
        """Generate description using AI in background thread."""
        if not self.viewer_state.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return

        selected_model = self.ui_components.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return

        # Check if description generation is already running
        if self.ai_threads['description'] and self.ai_threads['description'].is_alive():
            # Cancel current generation
            with self.generation_lock:
                self.ai_cancelled['description'] = True
                # If Generate All is active, cancel it too
                if self._generate_all_active:
                    self._generate_all_active = False
                    logging.debug("Individual description cancellation triggered Generate All cancellation")
                    # Let finally blocks handle cleanup when Generate All is active
                    return

            # Not under Generate All - reset immediately
            self.ui_components.desc_generate_button.configure(text="Generate", state="normal")
            self.ai_threads['description'] = None
            return

        # Start generation in background thread with unique generation ID
        with self.generation_lock:
            self.ai_cancelled['description'] = False
            self.generation_counter['description'] += 1
            generation_id = self.generation_counter['description']
            self.current_generation_id['description'] = generation_id

        self.ai_threads['description'] = threading.Thread(
            target=self._generate_description_worker,
            args=(selected_model, generation_id),
            daemon=True
        )
        self.ui_components.desc_generate_button.configure(text="Cancel")
        self.ai_threads['description'].start()
        logging.debug(f"Started description generation with ID {generation_id}")

    def _generate_description_worker(self, selected_model: str, generation_id: int):
        """Worker thread for description generation."""
        try:
            # Get AI provider from config
            from shared.config import get_config
            from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator

            config = get_config()
            available_models = config.get_available_ai_models()

            # Find model key
            model_key = None
            for model in available_models:
                if model["display_name"] == selected_model:
                    model_key = model["key"]
                    break

            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")

            # Check for cancellation
            with self.generation_lock:
                cancelled = self.ai_cancelled['description']
            if cancelled:
                self.root.after(0, self._update_description_result, None, None, generation_id)
                return

            # Handle editorial metadata if needed
            editorial_data = None
            if self.viewer_state.editorial_var.get():
                # Extract editorial metadata from EXIF
                extracted_data, missing_fields = extract_editorial_metadata_from_exif(
                    self.viewer_state.current_file_path
                )

                # Check if we need user input for missing fields
                if any(missing_fields.values()):
                    # Show dialog synchronously and wait for result
                    editorial_data = self._show_editorial_dialog_sync(missing_fields, extracted_data)
                    if editorial_data is None:
                        # User cancelled - stop generation
                        return
                    # Merge with extracted data
                    editorial_data = {**extracted_data, **editorial_data}
                else:
                    editorial_data = extracted_data

            # Create generator and generate description (returns str for original only)
            generator = create_metadata_generator(model_key)
            existing_title = self.viewer_state.title_entry.get().strip()
            existing_desc = self.viewer_state.desc_text.get('1.0', 'end').strip()

            description = generator.generate_description(
                self.viewer_state.current_file_path,
                existing_title if existing_title else None,
                existing_desc if existing_desc else None,
                editorial_data
            )

            # Check for cancellation before updating UI
            with self.generation_lock:
                cancelled = self.ai_cancelled['description']
            if cancelled:
                self.root.after(0, self._update_description_result, None, None, generation_id)
                return

            # Update UI in main thread with generated description
            self.root.after(0, self._update_description_result, description, None, generation_id)

        except Exception as e:
            logging.error(f"Description generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_description_result, None, str(e), generation_id)

    def _update_description_result(self, description: Optional[str], error: Optional[str], generation_id: int):
        """Update UI with description generation result (called in main thread)."""
        try:
            # Check if this result is from the current generation
            with self.generation_lock:
                is_current = (generation_id == self.current_generation_id['description'])
                cancelled = self.ai_cancelled['description']

            if not is_current:
                logging.debug(f"Description generation {generation_id} is stale (current: {self.current_generation_id['description']}) - ignoring result")
                return

            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate description: {error}")
            else:
                if description and not cancelled:
                    self.viewer_state.desc_text.delete('1.0', 'end')
                    self.viewer_state.desc_text.insert('1.0', description)
                    self.viewer_state.on_description_change()
                    logging.debug(f"Description generation {generation_id} completed successfully")
        finally:
            # Reset button only if no new thread is running AND not running under Generate All
            with self.generation_lock:
                is_generate_all_active = self._generate_all_active
                is_current = (generation_id == self.current_generation_id['description'])

            # Only reset button if this is still the current generation
            if is_current and not (self.ai_threads['description'] and self.ai_threads['description'].is_alive()):
                # If Generate All is NOT active, reset button to normal state
                # If Generate All IS active, button will be reset by Generate All completion
                if not is_generate_all_active:
                    self.ui_components.desc_generate_button.configure(text="Generate", state="normal")

    def _show_editorial_dialog_sync(self, missing_fields: Dict[str, bool], extracted_data: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Show editorial dialog synchronously from worker thread."""
        # Create result container and event for synchronization
        result_container = {'result': None}
        dialog_completed = threading.Event()

        def show_dialog_in_main_thread():
            """Show dialog in main thread and store result."""
            try:
                result_container['result'] = get_editorial_metadata(self.root, missing_fields, extracted_data)
            except Exception as e:
                logging.error(f"Editorial dialog error: {e}")
                result_container['result'] = None
            finally:
                dialog_completed.set()

        # Schedule dialog to show in main thread
        self.root.after(0, show_dialog_in_main_thread)

        # Wait for dialog completion (blocks worker thread)
        dialog_completed.wait()

        return result_container['result']

    def generate_keywords(self):
        """Generate keywords using AI in background thread."""
        if not self.viewer_state.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return

        selected_model = self.ui_components.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return

        # Check if keywords generation is already running
        if self.ai_threads['keywords'] and self.ai_threads['keywords'].is_alive():
            # Cancel current generation
            with self.generation_lock:
                self.ai_cancelled['keywords'] = True
                # If Generate All is active, cancel it too
                if self._generate_all_active:
                    self._generate_all_active = False
                    logging.debug("Individual keywords cancellation triggered Generate All cancellation")
                    # Let finally blocks handle cleanup when Generate All is active
                    return

            # Not under Generate All - reset immediately
            self.ui_components.keywords_generate_button.configure(text="Generate", state="normal")
            self.ai_threads['keywords'] = None
            return

        # Start generation in background thread with unique generation ID
        with self.generation_lock:
            self.ai_cancelled['keywords'] = False
            self.generation_counter['keywords'] += 1
            generation_id = self.generation_counter['keywords']
            self.current_generation_id['keywords'] = generation_id

        self.ai_threads['keywords'] = threading.Thread(
            target=self._generate_keywords_worker,
            args=(selected_model, generation_id),
            daemon=True
        )
        self.ui_components.keywords_generate_button.configure(text="Cancel")
        self.ai_threads['keywords'].start()
        logging.debug(f"Started keywords generation with ID {generation_id}")

    def _generate_keywords_worker(self, selected_model: str, generation_id: int):
        """Worker thread for keywords generation."""
        try:
            # Get AI provider from config
            from shared.config import get_config
            from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator

            config = get_config()
            available_models = config.get_available_ai_models()

            # Find model key
            model_key = None
            for model in available_models:
                if model["display_name"] == selected_model:
                    model_key = model["key"]
                    break

            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")

            # Check for cancellation
            with self.generation_lock:
                cancelled = self.ai_cancelled['keywords']
            if cancelled:
                self.root.after(0, self._update_keywords_result, None, None, generation_id)
                return

            # Create generator and generate keywords (returns List[str] for original only)
            generator = create_metadata_generator(model_key)
            existing_title = self.viewer_state.title_entry.get().strip()
            existing_desc = self.viewer_state.desc_text.get('1.0', 'end').strip()

            # Ask for keyword count
            keyword_count = min(50, 50 - len(self.viewer_state.keywords_list))  # Don't exceed 50 total

            keywords = generator.generate_keywords(
                self.viewer_state.current_file_path,
                existing_title if existing_title else None,
                existing_desc if existing_desc else None,
                keyword_count,
                self.viewer_state.editorial_var.get()  # Pass editorial flag
            )

            # Check for cancellation before updating UI
            with self.generation_lock:
                cancelled = self.ai_cancelled['keywords']
            if cancelled:
                self.root.after(0, self._update_keywords_result, None, None, generation_id)
                return

            # Update UI in main thread with generated keywords
            self.root.after(0, self._update_keywords_result, keywords, None, generation_id)

        except Exception as e:
            logging.error(f"Keywords generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_keywords_result, None, str(e), generation_id)

    def _update_keywords_result(self, keywords: Optional[List[str]], error: Optional[str], generation_id: int):
        """Update UI with keywords generation result (called in main thread)."""
        try:
            # Check if this result is from the current generation
            with self.generation_lock:
                is_current = (generation_id == self.current_generation_id['keywords'])
                cancelled = self.ai_cancelled['keywords']

            if not is_current:
                logging.debug(f"Keywords generation {generation_id} is stale (current: {self.current_generation_id['keywords']}) - ignoring result")
                return

            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate keywords: {error}")
            else:
                if keywords and not cancelled:
                    # Add keywords to existing list (avoiding duplicates)
                    for keyword in keywords:
                        if keyword not in self.viewer_state.keywords_list and len(self.viewer_state.keywords_list) < 50:
                            self.viewer_state.keywords_list.append(keyword)

                    # Update UI
                    self.viewer_state.refresh_keywords_display()
                    logging.debug(f"Keywords generation {generation_id} completed successfully")
        finally:
            # Reset button only if no new thread is running AND not running under Generate All
            with self.generation_lock:
                is_generate_all_active = self._generate_all_active
                is_current = (generation_id == self.current_generation_id['keywords'])

            # Only reset button if this is still the current generation
            if is_current and not (self.ai_threads['keywords'] and self.ai_threads['keywords'].is_alive()):
                # If Generate All is NOT active, reset button to normal state
                # If Generate All IS active, button will be reset by Generate All completion
                if not is_generate_all_active:
                    self.ui_components.keywords_generate_button.configure(text="Generate", state="normal")

    def generate_categories(self):
        """Generate categories using AI in background thread."""
        if not self.viewer_state.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return

        selected_model = self.ui_components.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return

        if not self.categories_manager.category_combos:
            messagebox.showinfo("No Categories", "No category dropdowns available to populate")
            return

        # Check if categories generation is already running
        if self.ai_threads['categories'] and self.ai_threads['categories'].is_alive():
            # Cancel current generation
            with self.generation_lock:
                self.ai_cancelled['categories'] = True
                # If Generate All is active, cancel it too
                if self._generate_all_active:
                    self._generate_all_active = False
                    logging.debug("Individual categories cancellation triggered Generate All cancellation")
                    # Let finally blocks handle cleanup when Generate All is active
                    return

            # Not under Generate All - reset immediately
            self.ui_components.categories_generate_button.configure(text="Generate", state="normal")
            self.ai_threads['categories'] = None
            return

        # Start generation in background thread with unique generation ID
        with self.generation_lock:
            self.ai_cancelled['categories'] = False
            self.generation_counter['categories'] += 1
            generation_id = self.generation_counter['categories']
            self.current_generation_id['categories'] = generation_id

        self.ai_threads['categories'] = threading.Thread(
            target=self._generate_categories_worker,
            args=(selected_model, generation_id),
            daemon=True
        )
        self.ui_components.categories_generate_button.configure(text="Cancel")
        self.ai_threads['categories'].start()
        logging.debug(f"Started categories generation with ID {generation_id}")

    def _generate_categories_worker(self, selected_model: str, generation_id: int):
        """Worker thread for categories generation."""
        try:
            # Get AI provider from config
            from shared.config import get_config
            from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator

            config = get_config()
            available_models = config.get_available_ai_models()

            # Find model key
            model_key = None
            for model in available_models:
                if model["display_name"] == selected_model:
                    model_key = model["key"]
                    break

            if not model_key:
                raise ValueError(f"Model key not found for: {selected_model}")

            # Check for cancellation
            with self.generation_lock:
                cancelled = self.ai_cancelled['categories']
            if cancelled:
                self.root.after(0, self._update_categories_result, None, None, generation_id)
                return

            # Create generator and set categories
            generator = create_metadata_generator(model_key)
            generator.set_photobank_categories(self.photobank_categories)

            existing_title = self.viewer_state.title_entry.get().strip()
            existing_desc = self.viewer_state.desc_text.get('1.0', 'end').strip()

            # Generate categories for all photobanks
            generated_categories = generator.generate_categories(
                self.viewer_state.current_file_path,
                existing_title if existing_title else None,
                existing_desc if existing_desc else None
            )

            # Check for cancellation before updating UI
            with self.generation_lock:
                cancelled = self.ai_cancelled['categories']
            if cancelled:
                self.root.after(0, self._update_categories_result, None, None, generation_id)
                return

            # Update UI in main thread
            self.root.after(0, self._update_categories_result, generated_categories, None, generation_id)

        except Exception as e:
            logging.error(f"Categories generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_categories_result, None, str(e), generation_id)

    def _update_categories_result(self, generated_categories: Optional[Dict], error: Optional[str], generation_id: int):
        """Update UI with categories generation result (called in main thread)."""
        try:
            # Check if this result is from the current generation
            with self.generation_lock:
                is_current = (generation_id == self.current_generation_id['categories'])
                cancelled = self.ai_cancelled['categories']

            if not is_current:
                logging.debug(f"Categories generation {generation_id} is stale (current: {self.current_generation_id['categories']}) - ignoring result")
                return

            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate categories: {error}")
            else:
                if generated_categories and not cancelled:
                    # Update UI dropdowns with generated categories
                    self.categories_manager.update_categories(generated_categories)
                    logging.debug(f"Categories generation {generation_id} completed successfully")
        finally:
            # Reset button only if no new thread is running AND not running under Generate All
            with self.generation_lock:
                is_generate_all_active = self._generate_all_active
                is_current = (generation_id == self.current_generation_id['categories'])

            # Only reset button if this is still the current generation
            if is_current and not (self.ai_threads['categories'] and self.ai_threads['categories'].is_alive()):
                # If Generate All is NOT active, reset button to normal state
                # If Generate All IS active, button will be reset by Generate All completion
                if not is_generate_all_active:
                    self.ui_components.categories_generate_button.configure(text="Generate", state="normal")

    def generate_all_metadata(self):
        """Generate all metadata serially with proper dependencies."""
        if not self.viewer_state.current_file_path:
            messagebox.showwarning("No File", "No media file loaded")
            return

        selected_model = self.ui_components.model_combo.get()
        if not selected_model or selected_model in ["No models available", "Error loading models"]:
            messagebox.showwarning("No Model", "Please select a valid AI model")
            return

        # Check if Generate All is already active - if so, cancel
        cancelled = False
        with self.generation_lock:
            if self._generate_all_active:
                # Cancel inside lock (don't call _cancel_all_generation which tries to acquire lock again)
                for gen_type in ['title', 'description', 'keywords', 'categories']:
                    self.ai_cancelled[gen_type] = True
                self._generate_all_active = False
                cancelled = True

        # If we cancelled, immediately reset ALL buttons and clear thread references
        if cancelled:
            # Clear all thread references immediately (let daemon threads die naturally via cancellation flags)
            for gen_type in ['title', 'description', 'keywords', 'categories']:
                self.ai_threads[gen_type] = None

            # Reset ALL buttons immediately (both Generate All and individual buttons)
            self.ui_components.generate_all_button.configure(text="Generate All", state="normal")
            self.ui_components.title_generate_button.configure(text="Generate", state="normal")
            self.ui_components.desc_generate_button.configure(text="Generate", state="normal")
            self.ui_components.keywords_generate_button.configure(text="Generate", state="normal")
            self.ui_components.categories_generate_button.configure(text="Generate", state="normal")

            if hasattr(self, 'update_all_button_states_callback'):
                self.update_all_button_states_callback()
            logging.debug("All generations cancelled - buttons reset immediately")
            return

        # Start serial generation in background thread
        with self.generation_lock:
            self._generate_all_active = True
            thread = threading.Thread(
                target=self._generate_all_worker,
                args=(selected_model,),
                daemon=True
            )
            self.ai_threads['all'] = thread

        self.ui_components.generate_all_button.configure(text="Cancel", state="normal")

        # Start OUTSIDE lock
        thread.start()

    def _should_run_generation(self, gen_type: str) -> bool:
        """
        Check if a generation should run based on button state.

        Args:
            gen_type: Type of generation ('title', 'description', 'keywords', 'categories')

        Returns:
            True if generation should run
        """
        # Delegate to metadata_validator's should_enable_generation_button
        if hasattr(self, 'should_enable_generation_button_callback'):
            return self.should_enable_generation_button_callback(gen_type)
        return False

    def _generate_all_worker(self, selected_model: str):
        """Worker thread that runs all generations serially with join()."""
        try:
            # Reset all cancellation flags
            with self.generation_lock:
                for gen_type in ['title', 'description', 'keywords', 'categories']:
                    self.ai_cancelled[gen_type] = False

            # Generate title and wait for completion (if button is enabled)
            if self._should_run_generation('title'):
                logging.debug("Generate All: Running title generation")
                self._start_and_wait_for_generation('title', selected_model)
                with self.generation_lock:
                    should_continue = self._generate_all_active and not self.ai_cancelled['title']
                if not should_continue:
                    return
            else:
                logging.debug("Generate All: Skipping title generation (button disabled)")

            # Generate description and wait for completion (if button is enabled)
            if self._should_run_generation('description'):
                logging.debug("Generate All: Running description generation")
                self._start_and_wait_for_generation('description', selected_model)
                with self.generation_lock:
                    should_continue = self._generate_all_active and not self.ai_cancelled['description']
                if not should_continue:
                    return
            else:
                logging.debug("Generate All: Skipping description generation (button disabled)")

            # Generate keywords and wait for completion (if button is enabled)
            if self._should_run_generation('keywords'):
                logging.debug("Generate All: Running keywords generation")
                self._start_and_wait_for_generation('keywords', selected_model)
                with self.generation_lock:
                    should_continue = self._generate_all_active and not self.ai_cancelled['keywords']
                if not should_continue:
                    return
            else:
                logging.debug("Generate All: Skipping keywords generation (button disabled)")

            # Generate categories and wait for completion (if button is enabled)
            if self._should_run_generation('categories'):
                logging.debug("Generate All: Running categories generation")
                self._start_and_wait_for_generation('categories', selected_model)
                with self.generation_lock:
                    should_continue = self._generate_all_active and not self.ai_cancelled['categories']
                if not should_continue:
                    return
            else:
                logging.debug("Generate All: Skipping categories generation (button disabled)")

            # All completed successfully
            self.root.after(0, self._complete_all_generation)

        except Exception as e:
            logging.error(f"Generate All failed: {e}")
            self.root.after(0, self._complete_all_generation)

        finally:
            # Always ensure Generate All is marked inactive
            with self.generation_lock:
                self._generate_all_active = False
            logging.debug("Generate All worker cleanup: _generate_all_active set to False")

    def _start_and_wait_for_generation(self, gen_type: str, selected_model: str):
        """Start a generation and wait for it to complete."""
        # Update UI in main thread - change button to Cancel
        if gen_type == 'title':
            self.root.after(0, lambda: self.ui_components.title_generate_button.configure(text="Cancel"))
        elif gen_type == 'description':
            self.root.after(0, lambda: self.ui_components.desc_generate_button.configure(text="Cancel"))
        elif gen_type == 'keywords':
            self.root.after(0, lambda: self.ui_components.keywords_generate_button.configure(text="Cancel"))
        elif gen_type == 'categories':
            self.root.after(0, lambda: self.ui_components.categories_generate_button.configure(text="Cancel"))

        # Generate unique generation ID for this type
        with self.generation_lock:
            self.generation_counter[gen_type] += 1
            generation_id = self.generation_counter[gen_type]
            self.current_generation_id[gen_type] = generation_id

        logging.debug(f"Generate All: Starting {gen_type} generation with ID {generation_id}")

        # Start the worker thread directly with generation ID
        if gen_type == 'title':
            with self.generation_lock:
                thread = threading.Thread(
                    target=self._generate_title_worker,
                    args=(selected_model, generation_id),
                    daemon=True
                )
                self.ai_threads['title'] = thread
            thread.start()
            thread.join()
        elif gen_type == 'description':
            with self.generation_lock:
                thread = threading.Thread(
                    target=self._generate_description_worker,
                    args=(selected_model, generation_id),
                    daemon=True
                )
                self.ai_threads['description'] = thread
            thread.start()
            thread.join()
        elif gen_type == 'keywords':
            with self.generation_lock:
                thread = threading.Thread(
                    target=self._generate_keywords_worker,
                    args=(selected_model, generation_id),
                    daemon=True
                )
                self.ai_threads['keywords'] = thread
            thread.start()
            thread.join()
        elif gen_type == 'categories':
            with self.generation_lock:
                thread = threading.Thread(
                    target=self._generate_categories_worker,
                    args=(selected_model, generation_id),
                    daemon=True
                )
                self.ai_threads['categories'] = thread
            thread.start()
            thread.join()

    def _cancel_all_generation(self):
        """Cancel all running generations and reset all buttons."""
        # Set cancellation flags for all types
        with self.generation_lock:
            for gen_type in ['title', 'description', 'keywords', 'categories']:
                self.ai_cancelled[gen_type] = True
            # Reset Generate All state
            self._generate_all_active = False

        # Reset all individual buttons to Generate state
        self.ui_components.title_generate_button.configure(text="Generate", state="normal")
        self.ui_components.desc_generate_button.configure(text="Generate", state="normal")
        self.ui_components.keywords_generate_button.configure(text="Generate", state="normal")
        self.ui_components.categories_generate_button.configure(text="Generate", state="normal")

        # Reset Generate All button
        self.ui_components.generate_all_button.configure(text="Generate All", state="normal")

        # Update button states to reflect actual availability
        if hasattr(self, 'update_all_button_states_callback'):
            self.update_all_button_states_callback()

        logging.debug("All generations cancelled")

    def _complete_all_generation(self):
        """Complete the generate all process."""
        with self.generation_lock:
            self._generate_all_active = False
        self.ui_components.generate_all_button.configure(text="Generate All", state="normal")
        # Update button states to reflect actual availability
        if hasattr(self, 'update_all_button_states_callback'):
            self.update_all_button_states_callback()
        logging.debug("All metadata generation completed")