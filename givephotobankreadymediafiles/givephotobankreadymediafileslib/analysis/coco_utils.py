"""
Utility functions for working with COCO categories.
"""

import logging
import os

import requests

from givephotobankreadymediafileslib.constants import COCO_CATEGORIES_FILE, COCO_CATEGORIES_URL


def load_coco_categories() -> list[str]:
    """
    Load COCO categories from the text file.

    Returns:
        List of COCO category names
    """
    try:
        # Check if the text file exists
        if not os.path.exists(COCO_CATEGORIES_FILE):
            logging.warning(f"COCO categories file not found at {COCO_CATEGORIES_FILE}")
            return []

        # Load the text file
        with open(COCO_CATEGORIES_FILE, encoding="utf-8") as f:
            categories = [line.strip() for line in f if line.strip()]

        if not categories:
            logging.warning("No categories found in COCO categories file")
            return []

        logging.info(f"Loaded {len(categories)} COCO categories from {COCO_CATEGORIES_FILE}")

        return categories

    except Exception as e:
        logging.error(f"Error loading COCO categories: {e}")
        return []


def download_coco_categories() -> bool:
    """
    Download COCO categories from the specified URL and save to a text file.

    Returns:
        True if download was successful, False otherwise
    """
    try:
        # Download the YAML file
        response = requests.get(COCO_CATEGORIES_URL, timeout=10)
        response.raise_for_status()

        # Parse the content
        content = response.text

        # Extract categories from the YAML content
        categories = []
        in_categories_section = False

        for line in content.split("\n"):
            line = line.strip()

            # Check if we're in the categories section
            if line.startswith("# Classes"):
                in_categories_section = True
                continue

            # Check if we've reached the end of the categories section
            if in_categories_section and line.startswith("# Download"):
                break

            # Parse category line
            if in_categories_section and ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    category = parts[1].strip()
                    categories.append(category)

        if not categories:
            logging.warning("No categories found in downloaded YAML")
            return False

        # Ensure the directory exists
        os.makedirs(os.path.dirname(COCO_CATEGORIES_FILE), exist_ok=True)

        # Save the categories to a plain text file, one per line
        with open(COCO_CATEGORIES_FILE, "w", encoding="utf-8") as f:
            for category in categories:
                f.write(f"{category}\n")

        logging.info(f"Downloaded and saved {len(categories)} COCO categories to {COCO_CATEGORIES_FILE}")
        return True

    except Exception as e:
        logging.error(f"Error downloading COCO categories: {e}")
        return False


def get_coco_categories(download_if_empty: bool = True) -> list[str]:
    """
    Get COCO categories, optionally downloading from URL if empty.

    Args:
        download_if_empty: Whether to download from URL if no categories are found

    Returns:
        List of COCO category names
    """
    # Default COCO categories in case we can't load or download them
    default_categories = [
        "person",
        "bicycle",
        "car",
        "motorcycle",
        "airplane",
        "bus",
        "train",
        "truck",
        "boat",
        "traffic light",
        "fire hydrant",
        "stop sign",
        "parking meter",
        "bench",
        "bird",
        "cat",
        "dog",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "bear",
        "zebra",
        "giraffe",
        "backpack",
        "umbrella",
        "handbag",
        "tie",
        "suitcase",
        "frisbee",
        "skis",
        "snowboard",
        "sports ball",
        "kite",
        "baseball bat",
        "baseball glove",
        "skateboard",
        "surfboard",
        "tennis racket",
        "bottle",
        "wine glass",
        "cup",
        "fork",
        "knife",
        "spoon",
        "bowl",
        "banana",
        "apple",
        "sandwich",
        "orange",
        "broccoli",
        "carrot",
        "hot dog",
        "pizza",
        "donut",
        "cake",
        "chair",
        "couch",
        "potted plant",
        "bed",
        "dining table",
        "toilet",
        "tv",
        "laptop",
        "mouse",
        "remote",
        "keyboard",
        "cell phone",
        "microwave",
        "oven",
        "toaster",
        "sink",
        "refrigerator",
        "book",
        "clock",
        "vase",
        "scissors",
        "teddy bear",
        "hair drier",
        "toothbrush",
    ]

    categories = load_coco_categories()

    if not categories and download_if_empty:
        logging.info("No COCO categories found, attempting to download from URL")
        download_success = download_coco_categories()

        if download_success:
            categories = load_coco_categories()

    # If still no categories, use default
    if not categories:
        logging.warning("Using default COCO categories")
        return default_categories

    return categories
