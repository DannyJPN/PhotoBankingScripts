"""
Online LLM-based metadata generator.
"""

import json
import logging
import re
from typing import Any

import numpy as np

from givephotobankreadymediafileslib.constants import (
    CATEGORIES_PROMPT,
    DESCRIPTION_PROMPT,
    KEYWORDS_PROMPT,
    TITLE_PROMPT,
)
from givephotobankreadymediafileslib.llm_online.api_llm import APILLMClient
from givephotobankreadymediafileslib.metadata.abstract_generator import AbstractMetadataGenerator


class OnlineLLMMetadataGenerator(AbstractMetadataGenerator):
    """
    Metadata generator using online LLM services.

    This class uses cloud-based language models to generate
    titles, descriptions, keywords, and categories for media files.
    """

    def __init__(self, provider: str = "openai", model_name: str = "gpt-4-vision", api_key: str | None = None):
        """
        Initialize the online LLM metadata generator.

        Args:
            provider: Name of the API provider ('openai', 'anthropic', 'google', etc.)
            model_name: Name of the model to use
            api_key: API key for the service (if None, will try to get from environment)
        """
        super().__init__(name=f"Online LLM ({provider})")
        self.provider = provider
        self.model_name = model_name

        # Initialize LLM client
        self.llm_client = APILLMClient(provider=provider, model_name=model_name, api_key=api_key)

        logging.info(f"Online LLM metadata generator initialized with {provider} {model_name}")

    def _parse_json_response(self, response: str, expected_keys: list[str]) -> dict[str, Any]:
        """
        Parse JSON response from LLM.

        Args:
            response: JSON response string from LLM
            expected_keys: List of expected keys in the JSON response

        Returns:
            Parsed JSON as dictionary
        """
        try:
            # Extract JSON from response (in case there's additional text)
            json_match = re.search(r"({.*})", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response

            # Parse JSON
            data = json.loads(json_str)

            # Check for expected keys
            for key in expected_keys:
                if key not in data:
                    logging.warning(f"Expected key '{key}' not found in LLM response")
                    data[key] = "" if key != "keywords" else []

            return data

        except Exception as e:
            logging.error(f"Error parsing LLM response: {e}")
            # Return empty dictionary with expected keys
            return {key: "" if key != "keywords" else [] for key in expected_keys}

    def generate_title(self, image_features: np.ndarray, **kwargs) -> str:
        """
        Generate a title using an online LLM model.

        Args:
            image_features: Feature vector extracted from the image
            **kwargs: Additional arguments

        Returns:
            Generated title string
        """
        try:
            # Get image data if available
            image_data = kwargs.get("image_data")

            # Create prompt
            prompt = TITLE_PROMPT

            # Generate title
            response = (
                self.llm_client.generate_text_with_image(prompt=prompt, image_data=image_data)
                if image_data
                else self.llm_client.generate_text(prompt=prompt)
            )

            # Parse response
            data = self._parse_json_response(response, ["title"])

            # Get title
            title = data.get("title", "Untitled")

            # Limit title length
            if len(title) > 80:
                title = title[:77] + "..."

            return title

        except Exception as e:
            logging.error(f"Error generating title with online LLM: {e}")
            return "Untitled"

    def generate_description(self, image_features: np.ndarray, title: str | None = None, **kwargs) -> str:
        """
        Generate a description using an online LLM model.

        Args:
            image_features: Feature vector extracted from the image
            title: Optional title to use as context
            **kwargs: Additional arguments

        Returns:
            Generated description string
        """
        try:
            # Get image data if available
            image_data = kwargs.get("image_data")

            # Create prompt
            prompt = DESCRIPTION_PROMPT
            if title:
                prompt = f"Title: {title}\n\n{prompt}"

            # Generate description
            response = (
                self.llm_client.generate_text_with_image(prompt=prompt, image_data=image_data)
                if image_data
                else self.llm_client.generate_text(prompt=prompt)
            )

            # Parse response
            data = self._parse_json_response(response, ["description"])

            # Get description
            description = data.get("description", "No description available.")

            # Limit description length
            if len(description) > 200:
                description = description[:197] + "..."

            return description

        except Exception as e:
            logging.error(f"Error generating description with online LLM: {e}")
            return "No description available."

    def generate_keywords(
        self, image_features: np.ndarray, title: str | None = None, description: str | None = None, **kwargs
    ) -> list[str]:
        """
        Generate keywords using an online LLM model.

        Args:
            image_features: Feature vector extracted from the image
            title: Optional title to use as context
            description: Optional description to use as context
            **kwargs: Additional arguments

        Returns:
            List of generated keywords
        """
        try:
            # Get image data if available
            image_data = kwargs.get("image_data")

            # Create prompt
            prompt = KEYWORDS_PROMPT
            context = []
            if title:
                context.append(f"Title: {title}")
            if description:
                context.append(f"Description: {description}")

            if context:
                prompt = "\n".join(context) + "\n\n" + prompt

            # Generate keywords
            response = (
                self.llm_client.generate_text_with_image(prompt=prompt, image_data=image_data)
                if image_data
                else self.llm_client.generate_text(prompt=prompt)
            )

            # Parse response
            data = self._parse_json_response(response, ["keywords"])

            # Get keywords
            keywords = data.get("keywords", [])

            # Ensure keywords is a list
            if isinstance(keywords, str):
                keywords = [kw.strip() for kw in keywords.split(",")]

            # Limit number of keywords
            if len(keywords) > 20:
                keywords = keywords[:20]

            return keywords

        except Exception as e:
            logging.error(f"Error generating keywords with online LLM: {e}")
            return []

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
        Generate a category using an online LLM model.

        Args:
            image_features: Feature vector extracted from the image
            photobank: Name of the photobank
            available_categories: List of available categories for the photobank
            title: Optional title to use as context
            description: Optional description to use as context
            **kwargs: Additional arguments

        Returns:
            Selected category string
        """
        try:
            # Get image data if available
            image_data = kwargs.get("image_data")

            # Create prompt with categories
            categories_str = ", ".join(available_categories)
            prompt = CATEGORIES_PROMPT.format(categories=categories_str)

            # Add context if available
            context = []
            if title:
                context.append(f"Title: {title}")
            if description:
                context.append(f"Description: {description}")

            if context:
                prompt = "\n".join(context) + "\n\n" + prompt

            # Generate category
            response = (
                self.llm_client.generate_text_with_image(prompt=prompt, image_data=image_data)
                if image_data
                else self.llm_client.generate_text(prompt=prompt)
            )

            # Parse response
            data = self._parse_json_response(response, ["category"])

            # Get category
            category = data.get("category", "")

            # Check if category is in available categories
            if category not in available_categories:
                logging.warning(f"Generated category '{category}' not in available categories")
                # Return first category as fallback
                return available_categories[0] if available_categories else ""

            return category

        except Exception as e:
            logging.error(f"Error generating category with online LLM: {e}")
            # Return first category as default
            return available_categories[0] if available_categories else ""
