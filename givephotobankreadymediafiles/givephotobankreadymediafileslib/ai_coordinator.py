"""
AI coordination module for MediaViewer.

Handles AI model selection, metadata generation, and threading.
"""

import logging
import traceback
import threading
import time
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
            self.ai_cancelled['title'] = True
            self.ui_components.title_generate_button.configure(text="Generate", state="normal")
            self.ai_threads['title'] = None  # Clear thread reference to allow restart
            return

        # Start generation in background thread
        self.ai_cancelled['title'] = False
        self.ai_threads['title'] = threading.Thread(
            target=self._generate_title_worker,
            args=(selected_model,),
            daemon=True
        )

        # Update UI for loading state
        self.ui_components.title_generate_button.configure(text="Cancel")

        self.ai_threads['title'].start()

    def _generate_title_worker(self, selected_model: str):
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
            if self.ai_cancelled['title']:
                self.root.after(0, self._update_title_result, None, None)
                return

            # Create generator and generate title (returns str for original only)
            generator = create_metadata_generator(model_key)
            existing_title = self.viewer_state.title_entry.get().strip()
            title = generator.generate_title(self.viewer_state.current_file_path,
                                            existing_title if existing_title else None)

            # Check for cancellation before updating UI
            if self.ai_cancelled['title']:
                self.root.after(0, self._update_title_result, None, None)
                return

            # Update UI in main thread with generated title
            self.root.after(0, self._update_title_result, title, None)

        except Exception as e:
            logging.error(f"Title generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_title_result, None, str(e))

    def _update_title_result(self, title: Optional[str], error: Optional[str]):
        """Update UI with title generation result (called in main thread)."""
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate title: {error}")
            elif title and not self.ai_cancelled['title']:
                self.viewer_state.title_entry.delete(0, 'end')
                self.viewer_state.title_entry.insert(0, title)
                self.viewer_state.on_title_change()
        finally:
            # Reset button only if no new thread is running
            if not (self.ai_threads['title'] and self.ai_threads['title'].is_alive()):
                self.ui_components.title_generate_button.configure(text="Generate", state="normal")
            # Update all button states after title generation completes
            if hasattr(self, 'update_all_button_states_callback'):
                self.update_all_button_states_callback()

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
            self.ai_cancelled['description'] = True
            self.ui_components.desc_generate_button.configure(text="Generate", state="normal")
            self.ai_threads['description'] = None  # Clear thread reference to allow restart
            return

        # Start generation in background thread
        self.ai_cancelled['description'] = False
        self.ai_threads['description'] = threading.Thread(
            target=self._generate_description_worker,
            args=(selected_model,),
            daemon=True
        )

        # Update UI for loading state
        self.ui_components.desc_generate_button.configure(text="Cancel")

        self.ai_threads['description'].start()

    def _generate_description_worker(self, selected_model: str):
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
            if self.ai_cancelled['description']:
                self.root.after(0, self._update_description_result, None, None)
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
            if self.ai_cancelled['description']:
                self.root.after(0, self._update_description_result, None, None)
                return

            # Update UI in main thread with generated description
            self.root.after(0, self._update_description_result, description, None)

        except Exception as e:
            logging.error(f"Description generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_description_result, None, str(e))

    def _update_description_result(self, description: Optional[str], error: Optional[str]):
        """Update UI with description generation result (called in main thread)."""
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate description: {error}")
            elif description and not self.ai_cancelled['description']:
                self.viewer_state.desc_text.delete('1.0', 'end')
                self.viewer_state.desc_text.insert('1.0', description)
                self.viewer_state.on_description_change()
        finally:
            # Reset button only if no new thread is running
            if not (self.ai_threads['description'] and self.ai_threads['description'].is_alive()):
                self.ui_components.desc_generate_button.configure(text="Generate", state="normal")
            # Update all button states after description generation completes
            if hasattr(self, 'update_all_button_states_callback'):
                self.update_all_button_states_callback()

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
            self.ai_cancelled['keywords'] = True
            self.ui_components.keywords_generate_button.configure(text="Generate", state="normal")
            self.ai_threads['keywords'] = None  # Clear thread reference to allow restart
            return

        # Start generation in background thread
        self.ai_cancelled['keywords'] = False
        self.ai_threads['keywords'] = threading.Thread(
            target=self._generate_keywords_worker,
            args=(selected_model,),
            daemon=True
        )

        # Update UI for loading state
        self.ui_components.keywords_generate_button.configure(text="Cancel")

        self.ai_threads['keywords'].start()

    def _generate_keywords_worker(self, selected_model: str):
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
            if self.ai_cancelled['keywords']:
                self.root.after(0, self._update_keywords_result, None, None)
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
            if self.ai_cancelled['keywords']:
                self.root.after(0, self._update_keywords_result, None, None)
                return

            # Update UI in main thread with generated keywords
            self.root.after(0, self._update_keywords_result, keywords, None)

        except Exception as e:
            logging.error(f"Keywords generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_keywords_result, None, str(e))

    def _update_keywords_result(self, keywords: Optional[List[str]], error: Optional[str]):
        """Update UI with keywords generation result (called in main thread)."""
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate keywords: {error}")
            elif keywords and not self.ai_cancelled['keywords']:
                # Add keywords to existing list (avoiding duplicates)
                for keyword in keywords:
                    if keyword not in self.viewer_state.keywords_list and len(self.viewer_state.keywords_list) < 50:
                        self.viewer_state.keywords_list.append(keyword)

                # Update UI
                self.viewer_state.refresh_keywords_display()
        finally:
            # Reset button only if no new thread is running
            if not (self.ai_threads['keywords'] and self.ai_threads['keywords'].is_alive()):
                self.ui_components.keywords_generate_button.configure(text="Generate", state="normal")
            # Update all button states after keywords generation completes
            if hasattr(self, 'update_all_button_states_callback'):
                self.update_all_button_states_callback()

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
            self.ai_cancelled['categories'] = True
            self.ui_components.categories_generate_button.configure(text="Generate", state="normal")
            self.ai_threads['categories'] = None  # Clear thread reference to allow restart
            return

        # Start generation in background thread
        self.ai_cancelled['categories'] = False
        self.ai_threads['categories'] = threading.Thread(
            target=self._generate_categories_worker,
            args=(selected_model,),
            daemon=True
        )

        # Update UI for loading state
        self.ui_components.categories_generate_button.configure(text="Cancel")

        self.ai_threads['categories'].start()

    def _generate_categories_worker(self, selected_model: str):
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
            if self.ai_cancelled['categories']:
                self.root.after(0, self._update_categories_result, None, None)
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
            if self.ai_cancelled['categories']:
                self.root.after(0, self._update_categories_result, None, None)
                return

            # Update UI in main thread
            self.root.after(0, self._update_categories_result, generated_categories, None)

        except Exception as e:
            logging.error(f"Categories generation failed: {e}")
            # Update UI with error in main thread
            self.root.after(0, self._update_categories_result, None, str(e))

    def _update_categories_result(self, generated_categories: Optional[Dict], error: Optional[str]):
        """Update UI with categories generation result (called in main thread)."""
        try:
            if error:
                messagebox.showerror("Generation Failed", f"Failed to generate categories: {error}")
            elif generated_categories and not self.ai_cancelled['categories']:
                # Update UI dropdowns with generated categories
                self.categories_manager.update_categories(generated_categories)
        finally:
            # Reset button only if no new thread is running
            if not (self.ai_threads['categories'] and self.ai_threads['categories'].is_alive()):
                self.ui_components.categories_generate_button.configure(text="Generate", state="normal")
            # Update all button states after categories generation completes
            if hasattr(self, 'update_all_button_states_callback'):
                self.update_all_button_states_callback()

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
        if self._generate_all_active:
            self._cancel_all_generation()
            return

        # Start serial generation in background thread
        self._generate_all_active = True
        self.ui_components.generate_all_button.configure(text="Cancel", state="normal")

        # Start generation in background thread to avoid blocking UI
        self.ai_threads['all'] = threading.Thread(
            target=self._generate_all_worker,
            args=(selected_model,),
            daemon=True
        )
        self.ai_threads['all'].start()

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
            for gen_type in ['title', 'description', 'keywords', 'categories']:
                self.ai_cancelled[gen_type] = False

            # Generate title and wait for completion (if button is enabled)
            if self._should_run_generation('title'):
                logging.debug("Generate All: Running title generation")
                self._start_and_wait_for_generation('title', selected_model)
                if not self._generate_all_active or self.ai_cancelled['title']:
                    return
            else:
                logging.debug("Generate All: Skipping title generation (button disabled)")

            # Generate description and wait for completion (if button is enabled)
            if self._should_run_generation('description'):
                logging.debug("Generate All: Running description generation")
                self._start_and_wait_for_generation('description', selected_model)
                if not self._generate_all_active or self.ai_cancelled['description']:
                    return
            else:
                logging.debug("Generate All: Skipping description generation (button disabled)")

            # Generate keywords and wait for completion (if button is enabled)
            if self._should_run_generation('keywords'):
                logging.debug("Generate All: Running keywords generation")
                self._start_and_wait_for_generation('keywords', selected_model)
                if not self._generate_all_active or self.ai_cancelled['keywords']:
                    return
            else:
                logging.debug("Generate All: Skipping keywords generation (button disabled)")

            # Generate categories and wait for completion (if button is enabled)
            if self._should_run_generation('categories'):
                logging.debug("Generate All: Running categories generation")
                self._start_and_wait_for_generation('categories', selected_model)
                if not self._generate_all_active or self.ai_cancelled['categories']:
                    return
            else:
                logging.debug("Generate All: Skipping categories generation (button disabled)")

            # All completed successfully
            self.root.after(0, self._complete_all_generation)

        except Exception as e:
            logging.error(f"Generate All failed: {e}")
            self.root.after(0, self._complete_all_generation)

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

        # Start the worker thread directly
        if gen_type == 'title':
            self.ai_threads['title'] = threading.Thread(
                target=self._generate_title_worker,
                args=(selected_model,),
                daemon=True
            )
            self.ai_threads['title'].start()
            self.ai_threads['title'].join()
        elif gen_type == 'description':
            self.ai_threads['description'] = threading.Thread(
                target=self._generate_description_worker,
                args=(selected_model,),
                daemon=True
            )
            self.ai_threads['description'].start()
            self.ai_threads['description'].join()
        elif gen_type == 'keywords':
            self.ai_threads['keywords'] = threading.Thread(
                target=self._generate_keywords_worker,
                args=(selected_model,),
                daemon=True
            )
            self.ai_threads['keywords'].start()
            self.ai_threads['keywords'].join()
        elif gen_type == 'categories':
            self.ai_threads['categories'] = threading.Thread(
                target=self._generate_categories_worker,
                args=(selected_model,),
                daemon=True
            )
            self.ai_threads['categories'].start()
            self.ai_threads['categories'].join()

    def _cancel_all_generation(self):
        """Cancel all running generations and reset all buttons."""
        # Set cancellation flags for all types
        for gen_type in ['title', 'description', 'keywords', 'categories']:
            self.ai_cancelled[gen_type] = True

        # Reset all individual buttons to Generate state
        self.ui_components.title_generate_button.configure(text="Generate", state="normal")
        self.ui_components.desc_generate_button.configure(text="Generate", state="normal")
        self.ui_components.keywords_generate_button.configure(text="Generate", state="normal")
        self.ui_components.categories_generate_button.configure(text="Generate", state="normal")

        # Reset Generate All state and button
        self._generate_all_active = False
        self.ui_components.generate_all_button.configure(text="Generate All", state="normal")

        # Update button states to reflect actual availability
        if hasattr(self, 'update_all_button_states_callback'):
            self.update_all_button_states_callback()

        logging.debug("All generations cancelled")

    def _complete_all_generation(self):
        """Complete the generate all process."""
        self._generate_all_active = False
        self.ui_components.generate_all_button.configure(text="Generate All", state="normal")
        # Update button states to reflect actual availability
        if hasattr(self, 'update_all_button_states_callback'):
            self.update_all_button_states_callback()
        logging.debug("All metadata generation completed")