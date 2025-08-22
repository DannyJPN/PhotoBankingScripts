"""
Base LLM client module for text generation.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from givephotobankreadymediafileslib.constants import DEFAULT_LLM_MAX_TOKENS, DEFAULT_LLM_TIMEOUT


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, timeout: int = DEFAULT_LLM_TIMEOUT):
        """
        Initialize the LLM client.

        Args:
            timeout: Timeout in seconds for LLM requests
        """
        self.timeout = timeout
        logging.debug(f"LLMClient initialized with timeout {timeout}s")

    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: int = DEFAULT_LLM_MAX_TOKENS) -> str:
        """
        Generate text based on a prompt.

        Args:
            prompt: Input prompt for text generation
            max_tokens: Maximum number of tokens to generate

        Returns:
            Generated text string
        """
        pass

    @abstractmethod
    def generate_with_image(self, prompt: str, image_path: str, max_tokens: int = DEFAULT_LLM_MAX_TOKENS) -> str:
        """
        Generate text based on a prompt and an image.

        Args:
            prompt: Input prompt for text generation
            image_path: Path to the image file
            max_tokens: Maximum number of tokens to generate

        Returns:
            Generated text string
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the LLM service is available.

        Returns:
            True if available, False otherwise
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of the LLM service.

        Returns:
            Name of the LLM service
        """
        pass

    @abstractmethod
    def supports_image_input(self) -> bool:
        """
        Check if the LLM service supports image input.

        Returns:
            True if image input is supported, False otherwise
        """
        pass


class LLMClientFactory:
    """Factory class for creating LLM clients."""

    @staticmethod
    def create_client(client_type: str, **kwargs) -> LLMClient | None:
        """
        Create an LLM client of the specified type.

        Args:
            client_type: Type of LLM client ('local' or 'api')
            **kwargs: Additional arguments for the client

        Returns:
            LLM client instance or None if creation fails
        """
        try:
            if client_type.lower() == "local":
                from givephotobankreadymediafileslib.llm_local.local_llm import LocalLLMClient

                return LocalLLMClient(**kwargs)
            elif client_type.lower() == "api":
                from givephotobankreadymediafileslib.llm_online.api_llm import APILLMClient

                return APILLMClient(**kwargs)
            else:
                logging.error(f"Unknown LLM client type: {client_type}")
                return None
        except Exception as e:
            logging.error(f"Error creating LLM client: {e}")
            return None

    @staticmethod
    def get_available_clients() -> list[dict[str, Any]]:
        """
        Get a list of available LLM clients.

        Returns:
            List of dictionaries with client information
        """
        clients = []

        # Check for local clients
        try:
            from givephotobankreadymediafileslib.llm_local.local_llm import LocalLLMClient

            local_models = LocalLLMClient.list_available_models()
            for model in local_models:
                clients.append(
                    {
                        "type": "local",
                        "name": model["name"],
                        "supports_image": model.get("supports_image", False),
                        "model_id": model.get("model_id", model["name"]),
                    }
                )
        except Exception as e:
            logging.warning(f"Error checking local LLM clients: {e}")

        # Check for API clients
        try:
            from givephotobankreadymediafileslib.llm_online.api_llm import APILLMClient

            api_models = APILLMClient.list_available_models()
            for model in api_models:
                clients.append(
                    {
                        "type": "api",
                        "name": model["name"],
                        "supports_image": model.get("supports_image", False),
                        "model_id": model.get("model_id", model["name"]),
                        "provider": model.get("provider", "unknown"),
                    }
                )
        except Exception as e:
            logging.warning(f"Error checking API LLM clients: {e}")

        return clients
