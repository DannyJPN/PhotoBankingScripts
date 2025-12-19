"""
Categories management module for MediaViewer.

Handles photobank category selection and management.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional

from givephotobankreadymediafileslib.constants import get_category_column, PHOTOBANK_CATEGORY_COUNTS


class CategoriesManager:
    """Manages photobank categories selection and UI."""

    def __init__(self, root: tk.Tk, categories: Dict[str, List[str]] = None):
        """
        Initialize categories manager.

        Args:
            root: Tkinter root window
            categories: Dictionary mapping photobank names to their category lists
        """
        self.root = root
        self.categories = categories or {}

        # UI widget references (set by ui_components module)
        self.categories_container: Optional[ttk.Frame] = None
        self.category_combos: Dict[str, List[ttk.Combobox]] = {}

    def populate_categories_ui(self):
        """Populate categories UI with dropdown lists for each photobank based on their actual needs."""
        self.category_combos = {}

        if not self.categories_container:
            logging.warning("Categories container not initialized")
            return

        if not self.categories:
            ttk.Label(self.categories_container,
                     text="No categories available").pack(pady=10)
            return

        # Get category counts from constants
        categories_count = PHOTOBANK_CATEGORY_COUNTS

        # Create UI for each photobank's categories in compact horizontal layout
        photobanks_with_categories = [(photobank, categories) for photobank, categories in self.categories.items()
                                    if categories_count.get(photobank.lower().replace(' ', '').replace('_', ''), 0) > 0]

        if not photobanks_with_categories:
            ttk.Label(self.categories_container, text="No categories available").pack(pady=10)
            return

        # Horizontal layout: all photobanks in one row
        row_frame = ttk.Frame(self.categories_container)
        row_frame.pack(fill=tk.X, pady=5)

        for i, (photobank, categories) in enumerate(photobanks_with_categories):
            photobank_key = photobank.lower().replace(' ', '').replace('_', '')
            max_categories = categories_count.get(photobank_key, 0)

            # Create compact frame for this photobank
            bank_frame = ttk.Frame(row_frame)
            bank_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)

            # Photobank label
            bank_label = ttk.Label(bank_frame, text=photobank)
            bank_label.pack(anchor=tk.W)

            # Create dropdowns for this photobank
            self.category_combos[photobank] = []
            for j in range(max_categories):
                combo = ttk.Combobox(bank_frame, values=[''] + categories,
                                   state="readonly", width=12)
                combo.pack(fill=tk.X, pady=1)
                combo.set('')  # Default to empty

                self.category_combos[photobank].append(combo)

    def load_existing_categories(self, record: dict):
        """
        Load existing categories from CSV record into UI dropdowns.

        Args:
            record: CSV record dictionary with metadata
        """
        if not self.category_combos:
            return

        # Load categories for each photobank
        for photobank, combos in self.category_combos.items():
            # Get category column name using constants
            category_column = get_category_column(photobank)
            category_value = record.get(category_column, '').strip()

            if category_value:
                # Split by comma for multiple categories
                categories_list = [cat.strip() for cat in category_value.split(',') if cat.strip()]

                # Set values for each dropdown
                for i, combo in enumerate(combos):
                    if i < len(categories_list):
                        category = categories_list[i]

                        # Find the category in combo values and select it
                        values = combo['values']
                        if category in values:
                            combo.set(category)
                            logging.debug(f"Loaded category for {photobank} [{i+1}]: {category}")

    def collect_selected_categories(self) -> Dict[str, List[str]]:
        """
        Collect currently selected categories from UI dropdowns.

        Returns:
            Dictionary mapping photobank names to lists of selected categories
        """
        selected_categories = {}

        if not self.category_combos:
            return selected_categories

        for photobank, combos in self.category_combos.items():
            selected_categories[photobank] = []
            for combo in combos:
                value = combo.get().strip()
                if value:  # Only add non-empty selections
                    selected_categories[photobank].append(value)

        return selected_categories

    def update_categories(self, generated_categories: Dict[str, List[str]]):
        """
        Update UI dropdowns with AI-generated categories.

        Args:
            generated_categories: Dictionary mapping photobank names to generated category lists
        """
        if not self.category_combos:
            return

        for photobank, categories in generated_categories.items():
            if photobank in self.category_combos:
                combos = self.category_combos[photobank]

                # Set categories in dropdowns
                for i, category in enumerate(categories):
                    if i < len(combos):
                        if category in combos[i]['values']:
                            combos[i].set(category)
                            logging.debug(f"Set category for {photobank} [{i+1}]: {category}")