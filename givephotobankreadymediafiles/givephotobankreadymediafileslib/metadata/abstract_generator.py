"""
Abstract metadata generator module defining the interface for all metadata generators.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class AbstractMetadataGenerator(ABC):
    """
    Abstract base class for all metadata generators.

    This class defines the interface that all metadata generators must implement,
    regardless of whether they use neural networks, local LLMs, or online LLMs.
    """

    def __init__(self, name: str):
        """
        Initialize the metadata generator.

        Args:
            name: Name of the generator for logging purposes
        """
        self.name = name
        logging.debug(f"Initialized {self.name} metadata generator")

    @abstractmethod
    def generate_title(self, image_features: np.ndarray, **kwargs) -> str:
        """
        Generate a title for the media file.

        Args:
            image_features: Feature vector extracted from the image
            **kwargs: Additional arguments specific to the implementation

        Returns:
            Generated title string
        """
        pass

    @abstractmethod
    def generate_description(self, image_features: np.ndarray, title: str | None = None, **kwargs) -> str:
        """
        Generate a description for the media file.

        Args:
            image_features: Feature vector extracted from the image
            title: Optional title to use as context for generating the description
            **kwargs: Additional arguments specific to the implementation

        Returns:
            Generated description string
        """
        pass

    @abstractmethod
    def generate_keywords(
        self, image_features: np.ndarray, title: str | None = None, description: str | None = None, **kwargs
    ) -> list[str]:
        """
        Generate keywords for the media file.

        Args:
            image_features: Feature vector extracted from the image
            title: Optional title to use as context for generating keywords
            description: Optional description to use as context for generating keywords
            **kwargs: Additional arguments specific to the implementation

        Returns:
            List of generated keywords
        """
        pass

    @abstractmethod
    def generate_category(
        self,
        image_features: np.ndarray,
        photobank: str,
        available_categories: list[str],
        title: str | None = None,
        description: str | None = None,
        **kwargs,
    ) -> str:
        """
        Generate a category for the media file for a specific photobank.

        Args:
            image_features: Feature vector extracted from the image
            photobank: Name of the photobank
            available_categories: List of available categories for the photobank
            title: Optional title to use as context for category selection
            description: Optional description to use as context for category selection
            **kwargs: Additional arguments specific to the implementation

        Returns:
            Selected category string
        """
        pass

    def generate_all_metadata(
        self,
        image_features: np.ndarray,
        photobank: str | None = None,
        available_categories: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Generate all metadata for the media file.

        Args:
            image_features: Feature vector extracted from the image
            photobank: Optional name of the photobank
            available_categories: Optional list of available categories for the photobank
            **kwargs: Additional arguments specific to the implementation

        Returns:
            Dictionary containing all generated metadata
        """
        # Generate title first
        title = self.generate_title(image_features, **kwargs)

        # Generate description using title as context
        description = self.generate_description(image_features, title=title, **kwargs)

        # Generate keywords using title and description as context
        keywords = self.generate_keywords(image_features, title=title, description=description, **kwargs)

        # Create metadata dictionary
        metadata = {"title": title, "description": description, "keywords": keywords}

        # Generate category if photobank and available_categories are provided
        if photobank and available_categories:
            category = self.generate_category(
                image_features,
                photobank=photobank,
                available_categories=available_categories,
                title=title,
                description=description,
                **kwargs,
            )
            metadata["category"] = category

        return metadata
