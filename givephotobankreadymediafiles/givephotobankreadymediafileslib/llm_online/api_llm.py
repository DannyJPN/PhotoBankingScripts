"""
API LLM client module for text generation using online API services.
"""

import base64
import logging
import os
from typing import Any

import requests

from givephotobankreadymediafileslib.constants import DEFAULT_LLM_MAX_TOKENS, DEFAULT_LLM_TIMEOUT
from givephotobankreadymediafileslib.llm_online.llm_client import LLMClient


class APILLMClient(LLMClient):
    """Client for online LLM API services like OpenAI, Anthropic, etc."""

    def __init__(
        self,
        provider: str = "openai",
        model_name: str = "gpt-3.5-turbo",
        api_key: str | None = None,
        timeout: int = DEFAULT_LLM_TIMEOUT,
    ):
        """
        Initialize the API LLM client.

        Args:
            provider: Name of the API provider ('openai', 'anthropic', 'google', etc.)
            model_name: Name of the model to use
            api_key: API key for the service (if None, will try to get from environment)
            timeout: Timeout in seconds for API requests
        """
        super().__init__(timeout)
        self.provider = provider.lower()
        self.model_name = model_name
        self.api_key = api_key or self._get_api_key_from_env()

        # Set up API endpoints based on provider
        self.endpoints = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "google": "https://generativelanguage.googleapis.com/v1",
            "mistral": "https://api.mistral.ai/v1",
        }

        logging.debug(f"APILLMClient initialized with provider {provider}, model {model_name}")

    def _get_api_key_from_env(self) -> str | None:
        """
        Get API key from environment variables.

        Returns:
            API key string or None if not found
        """
        env_var_names = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "mistral": "MISTRAL_API_KEY",
        }

        env_var = env_var_names.get(self.provider)
        if env_var:
            return os.environ.get(env_var)
        return None

    def generate_text(self, prompt: str, max_tokens: int = DEFAULT_LLM_MAX_TOKENS) -> str:
        """
        Generate text based on a prompt using an API LLM.

        Args:
            prompt: Input prompt for text generation
            max_tokens: Maximum number of tokens to generate

        Returns:
            Generated text string
        """
        if not self.api_key:
            logging.error(f"No API key available for {self.provider}")
            return ""

        try:
            if self.provider == "openai":
                return self._generate_text_openai(prompt, max_tokens)
            elif self.provider == "anthropic":
                return self._generate_text_anthropic(prompt, max_tokens)
            elif self.provider == "google":
                return self._generate_text_google(prompt, max_tokens)
            elif self.provider == "mistral":
                return self._generate_text_mistral(prompt, max_tokens)
            else:
                logging.error(f"Unsupported API provider: {self.provider}")
                return ""
        except Exception as e:
            logging.error(f"Error generating text with {self.provider} API: {e}")
            return ""

    def _generate_text_openai(self, prompt: str, max_tokens: int) -> str:
        """Generate text using OpenAI API."""
        try:
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            }

            response = requests.post(
                f"{self.endpoints['openai']}/chat/completions", headers=headers, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                logging.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logging.error(f"Error with OpenAI API: {e}")
            return ""

    def _generate_text_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Generate text using Anthropic API."""
        try:
            headers = {"Content-Type": "application/json", "x-api-key": self.api_key, "anthropic-version": "2023-06-01"}

            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            }

            response = requests.post(
                f"{self.endpoints['anthropic']}/messages", headers=headers, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                logging.error(f"Anthropic API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logging.error(f"Error with Anthropic API: {e}")
            return ""

    def _generate_text_google(self, prompt: str, max_tokens: int) -> str:
        """Generate text using Google API."""
        try:
            headers = {"Content-Type": "application/json"}

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7},
            }

            response = requests.post(
                f"{self.endpoints['google']}/models/{self.model_name}:generateContent?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                logging.error(f"Google API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logging.error(f"Error with Google API: {e}")
            return ""

    def _generate_text_mistral(self, prompt: str, max_tokens: int) -> str:
        """Generate text using Mistral API."""
        try:
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            }

            response = requests.post(
                f"{self.endpoints['mistral']}/chat/completions", headers=headers, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                logging.error(f"Mistral API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logging.error(f"Error with Mistral API: {e}")
            return ""

    def generate_with_image(self, prompt: str, image_path: str, max_tokens: int = DEFAULT_LLM_MAX_TOKENS) -> str:
        """
        Generate text based on a prompt and an image using an API LLM.

        Args:
            prompt: Input prompt for text generation
            image_path: Path to the image file
            max_tokens: Maximum number of tokens to generate

        Returns:
            Generated text string
        """
        if not self.api_key:
            logging.error(f"No API key available for {self.provider}")
            return ""

        if not self.supports_image_input():
            logging.warning(f"Provider {self.provider} with model {self.model_name} does not support image input")
            return self.generate_text(prompt, max_tokens)

        try:
            # Load and encode the image
            with open(image_path, "rb") as img_file:
                image_data = base64.b64encode(img_file.read()).decode("utf-8")

            if self.provider == "openai":
                return self._generate_with_image_openai(prompt, image_data, max_tokens)
            elif self.provider == "google":
                return self._generate_with_image_google(prompt, image_path, max_tokens)
            else:
                logging.warning(f"Image input not supported for provider {self.provider}")
                return self.generate_text(prompt, max_tokens)
        except Exception as e:
            logging.error(f"Error generating text with image: {e}")
            return ""

    def _generate_with_image_openai(self, prompt: str, image_data: str, max_tokens: int) -> str:
        """Generate text with image using OpenAI API."""
        try:
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                        ],
                    }
                ],
                "max_tokens": max_tokens,
            }

            response = requests.post(
                f"{self.endpoints['openai']}/chat/completions", headers=headers, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                logging.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logging.error(f"Error with OpenAI API: {e}")
            return ""

    def _generate_with_image_google(self, prompt: str, image_path: str, max_tokens: int) -> str:
        """Generate text with image using Google API."""
        try:
            # For Google, we need to send the image as a file
            with open(image_path, "rb") as img_file:
                image_bytes = img_file.read()

            # Convert to base64
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            headers = {"Content-Type": "application/json"}

            payload = {
                "contents": [
                    {"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}}]}
                ],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7},
            }

            response = requests.post(
                f"{self.endpoints['google']}/models/{self.model_name}:generateContent?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                logging.error(f"Google API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logging.error(f"Error with Google API: {e}")
            return ""

    def is_available(self) -> bool:
        """
        Check if the API LLM service is available.

        Returns:
            True if available, False otherwise
        """
        if not self.api_key:
            return False

        try:
            # Simple ping to check if the API is accessible
            if self.provider == "openai":
                response = requests.get(
                    f"{self.endpoints['openai']}/models", headers={"Authorization": f"Bearer {self.api_key}"}, timeout=2
                )
                return response.status_code == 200
            elif self.provider == "anthropic":
                response = requests.get(
                    f"{self.endpoints['anthropic']}/models",
                    headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                    timeout=2,
                )
                return response.status_code == 200
            elif self.provider == "mistral":
                response = requests.get(
                    f"{self.endpoints['mistral']}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=2,
                )
                return response.status_code == 200
            else:
                # For other providers, just assume it's available if we have an API key
                return True
        except:
            return False

    def get_name(self) -> str:
        """
        Get the name of the LLM service.

        Returns:
            Name of the LLM service
        """
        return f"{self.provider.capitalize()} - {self.model_name}"

    def supports_image_input(self) -> bool:
        """
        Check if the API LLM model supports image input.

        Returns:
            True if image input is supported, False otherwise
        """
        # OpenAI multimodal models
        if self.provider == "openai":
            multimodal_models = ["gpt-4-vision", "gpt-4o", "gpt-4-turbo"]
            return any(mm in self.model_name.lower() for mm in multimodal_models)

        # Google multimodal models
        elif self.provider == "google":
            multimodal_models = ["gemini-pro-vision", "gemini-1.5-pro"]
            return any(mm in self.model_name.lower() for mm in multimodal_models)

        # Other providers don't support image input yet
        return False

    @staticmethod
    def list_available_models() -> list[dict[str, Any]]:
        """
        List available API LLM models.

        Returns:
            List of dictionaries with model information
        """
        models = []

        # OpenAI models
        if os.environ.get("OPENAI_API_KEY"):
            models.extend(
                [
                    {
                        "name": "OpenAI - GPT-3.5 Turbo",
                        "model_id": "gpt-3.5-turbo",
                        "provider": "openai",
                        "supports_image": False,
                    },
                    {"name": "OpenAI - GPT-4o", "model_id": "gpt-4o", "provider": "openai", "supports_image": True},
                    {
                        "name": "OpenAI - GPT-4 Turbo",
                        "model_id": "gpt-4-turbo",
                        "provider": "openai",
                        "supports_image": True,
                    },
                ]
            )

        # Anthropic models
        if os.environ.get("ANTHROPIC_API_KEY"):
            models.extend(
                [
                    {
                        "name": "Anthropic - Claude 3 Opus",
                        "model_id": "claude-3-opus-20240229",
                        "provider": "anthropic",
                        "supports_image": False,
                    },
                    {
                        "name": "Anthropic - Claude 3 Sonnet",
                        "model_id": "claude-3-sonnet-20240229",
                        "provider": "anthropic",
                        "supports_image": False,
                    },
                    {
                        "name": "Anthropic - Claude 3 Haiku",
                        "model_id": "claude-3-haiku-20240307",
                        "provider": "anthropic",
                        "supports_image": False,
                    },
                ]
            )

        # Google models
        if os.environ.get("GOOGLE_API_KEY"):
            models.extend(
                [
                    {
                        "name": "Google - Gemini Pro",
                        "model_id": "gemini-pro",
                        "provider": "google",
                        "supports_image": False,
                    },
                    {
                        "name": "Google - Gemini Pro Vision",
                        "model_id": "gemini-pro-vision",
                        "provider": "google",
                        "supports_image": True,
                    },
                    {
                        "name": "Google - Gemini 1.5 Pro",
                        "model_id": "gemini-1.5-pro",
                        "provider": "google",
                        "supports_image": True,
                    },
                ]
            )

        # Mistral models
        if os.environ.get("MISTRAL_API_KEY"):
            models.extend(
                [
                    {
                        "name": "Mistral - Mistral Large",
                        "model_id": "mistral-large-latest",
                        "provider": "mistral",
                        "supports_image": False,
                    },
                    {
                        "name": "Mistral - Mistral Medium",
                        "model_id": "mistral-medium-latest",
                        "provider": "mistral",
                        "supports_image": False,
                    },
                    {
                        "name": "Mistral - Mistral Small",
                        "model_id": "mistral-small-latest",
                        "provider": "mistral",
                        "supports_image": False,
                    },
                ]
            )

        return models
