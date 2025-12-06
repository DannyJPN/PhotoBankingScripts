"""
Categories management for photobanks.

This module handles:
- Category configuration per photobank
- Category UI creation and population
- Loading and saving category selections
- Category validation
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk

from givephotobankreadymediafileslib.constants import get_category_column


@dataclass
class CategoryConfig:
    """
    Category configuration for a photobank.

    :param photobank_name: Name of the photobank
    :param max_categories: Maximum number of categories allowed
    :param available_categories: List of available category names
    """

    photobank_name: str
    max_categories: int
    available_categories: List[str]


# Category counts per photobank based on 2025 research
PHOTOBANK_CATEGORY_COUNTS: Dict[str, int] = {
    'shutterstock': 2,      # Up to 2 categories
    'adobestock': 1,        # 1 category
    'dreamstime': 3,        # Up to 3 categories
    'alamy': 2,             # Primary + optional Secondary
    'depositphotos': 0,     # No categories
    'bigstockphoto': 0,     # No categories
    '123rf': 0,             # No categories
    'canstockphoto': 0,     # No categories
    'pond5': 0,             # No categories
    'gettyimages': 0        # No categories
}


def get_photobank_category_count(photobank: str) -> int:
    """
    Get the number of categories allowed for a photobank.

    :param photobank: Photobank name
    :return: Number of categories allowed (0 if not supported)
    """
    photobank_key = photobank.lower().replace(' ', '').replace('_', '')
    return PHOTOBANK_CATEGORY_COUNTS.get(photobank_key, 0)


def create_category_config(
    photobank_name: str,
    available_categories: List[str]
) -> Optional[CategoryConfig]:
    """
    Create category configuration for a photobank.

    :param photobank_name: Name of the photobank
    :param available_categories: List of available category names
    :return: CategoryConfig or None if photobank doesn't support categories
    """
    max_categories = get_photobank_category_count(photobank_name)

    if max_categories == 0:
        return None

    return CategoryConfig(
        photobank_name=photobank_name,
        max_categories=max_categories,
        available_categories=available_categories
    )


def filter_photobanks_with_categories(
    all_categories: Dict[str, List[str]]
) -> List[tuple[str, List[str]]]:
    """
    Filter photobanks that support categories.

    :param all_categories: Dict of photobank -> list of categories
    :return: List of (photobank, categories) tuples for photobanks with category support
    """
    photobanks_with_categories = []

    for photobank, categories in all_categories.items():
        if get_photobank_category_count(photobank) > 0:
            photobanks_with_categories.append((photobank, categories))

    return photobanks_with_categories


def create_category_comboboxes(
    parent_frame: ttk.Frame,
    photobank: str,
    categories: List[str]
) -> List[ttk.Combobox]:
    """
    Create category combobox widgets for a photobank.

    :param parent_frame: Parent frame to place comboboxes in
    :param photobank: Photobank name
    :param categories: Available categories for this photobank
    :return: List of created combobox widgets
    """
    max_categories = get_photobank_category_count(photobank)
    comboboxes = []

    # Create frame for this photobank
    bank_frame = ttk.Frame(parent_frame)
    bank_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)

    # Photobank label
    bank_label = ttk.Label(bank_frame, text=photobank)
    bank_label.pack(anchor=tk.W)

    # Create dropdowns
    for _ in range(max_categories):
        combo = ttk.Combobox(
            bank_frame,
            values=[''] + categories,
            state="readonly",
            width=12
        )
        combo.pack(fill=tk.X, pady=1)
        combo.set('')  # Default to empty
        comboboxes.append(combo)

    return comboboxes


def load_categories_from_record(
    category_combos: Dict[str, List[ttk.Combobox]],
    record: dict
) -> None:
    """
    Load existing categories from CSV record into UI dropdowns.

    :param category_combos: Dict of photobank -> list of comboboxes
    :param record: CSV record containing category data
    """
    for photobank, combos in category_combos.items():
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


def collect_selected_categories(
    category_combos: Dict[str, List[ttk.Combobox]]
) -> Dict[str, List[str]]:
    """
    Collect selected categories from all comboboxes.

    :param category_combos: Dict of photobank -> list of comboboxes
    :return: Dict of photobank -> list of selected categories
    """
    selected_categories = {}

    for photobank, combos in category_combos.items():
        selected_categories[photobank] = []
        for combo in combos:
            value = combo.get().strip()
            if value:  # Only add non-empty selections
                selected_categories[photobank].append(value)

    return selected_categories


def set_generated_categories(
    category_combos: Dict[str, List[ttk.Combobox]],
    generated_categories: Dict[str, List[str]]
) -> None:
    """
    Set generated categories into combobox widgets.

    :param category_combos: Dict of photobank -> list of comboboxes
    :param generated_categories: Dict of photobank -> list of generated categories
    """
    for photobank, categories in generated_categories.items():
        if photobank in category_combos:
            combos = category_combos[photobank]

            # Set categories in dropdowns
            for i, category in enumerate(categories):
                if i < len(combos):
                    if category in combos[i]['values']:
                        combos[i].set(category)
                        logging.debug(f"Set category for {photobank} [{i+1}]: {category}")


def validate_category_selection(
    photobank: str,
    selected_categories: List[str]
) -> bool:
    """
    Validate that category selection doesn't exceed limits.

    :param photobank: Photobank name
    :param selected_categories: List of selected categories
    :return: True if valid, False otherwise
    """
    max_categories = get_photobank_category_count(photobank)
    return len(selected_categories) <= max_categories