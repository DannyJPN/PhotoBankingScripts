"""
Local LLM client module for text generation using locally installed models.
"""
import logging
import os
import json
import subprocess
import requests
from typing import Dict, Any, List, Optional, Union
import base64
from io import BytesIO
from PIL import Image

from core.llm_client import LLMClient
from core.constants import DEFAULT_LLM_TIMEOUT, DEFAULT_LLM_MAX_TOKENS


class LocalLLMClient(LLMClient):
    """Client for local LLM services like Ollama or LM Studio."""
    
    def __init__(self, model_name: str = "llama3", 
                 endpoint: str = "http://localhost:11434",
                 timeout: int = DEFAULT_LLM_TIMEOUT):
        """
        Initialize the local LLM client.
        
        Args:
            model_name: Name of the model to use
            endpoint: API endpoint for the local LLM service
            timeout: Timeout in seconds for LLM requests
        """
        super().__init__(timeout)
        self.model_name = model_name
        self.endpoint = endpoint
        self.service_type = self._detect_service_type()
        
        logging.debug(f"LocalLLMClient initialized with model {model_name} at {endpoint}")
    
    def _detect_service_type(self) -> str:
        """
        Detect the type of local LLM service.
        
        Returns:
            Service type string ('ollama', 'lmstudio', or 'unknown')
        """
        # Try Ollama endpoint
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=2)
            if response.status_code == 200:
                return "ollama"
        except:
            pass
        
        # Try LM Studio endpoint
        try:
            response = requests.get(f"{self.endpoint}/v1/models", timeout=2)
            if response.status_code == 200:
                return "lmstudio"
        except:
            pass
        
        return "unknown"
    
    def generate_text(self, prompt: str, max_tokens: int = DEFAULT_LLM_MAX_TOKENS) -> str:
        """
        Generate text based on a prompt using a local LLM.
        
        Args:
            prompt: Input prompt for text generation
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text string
        """
        if not self.is_available():
            logging.error(f"Local LLM service not available at {self.endpoint}")
            return ""
        
        try:
            if self.service_type == "ollama":
                return self._generate_text_ollama(prompt, max_tokens)
            elif self.service_type == "lmstudio":
                return self._generate_text_lmstudio(prompt, max_tokens)
            else:
                logging.error("Unknown local LLM service type")
                return ""
        except Exception as e:
            logging.error(f"Error generating text with local LLM: {e}")
            return ""
    
    def _generate_text_ollama(self, prompt: str, max_tokens: int) -> str:
        """Generate text using Ollama API."""
        try:
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                logging.error(f"Ollama API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logging.error(f"Error with Ollama API: {e}")
            return ""
    
    def _generate_text_lmstudio(self, prompt: str, max_tokens: int) -> str:
        """Generate text using LM Studio API."""
        try:
            response = requests.post(
                f"{self.endpoint}/v1/completions",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": False
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json().get("choices", [{}])[0].get("text", "")
            else:
                logging.error(f"LM Studio API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logging.error(f"Error with LM Studio API: {e}")
            return ""
    
    def generate_with_image(self, prompt: str, image_path: str, max_tokens: int = DEFAULT_LLM_MAX_TOKENS) -> str:
        """
        Generate text based on a prompt and an image using a local LLM.
        
        Args:
            prompt: Input prompt for text generation
            image_path: Path to the image file
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text string
        """
        if not self.is_available():
            logging.error(f"Local LLM service not available at {self.endpoint}")
            return ""
        
        if not self.supports_image_input():
            logging.warning(f"Local model {self.model_name} does not support image input")
            return self.generate_text(prompt, max_tokens)
        
        try:
            # Load and encode the image
            with open(image_path, "rb") as img_file:
                image_data = base64.b64encode(img_file.read()).decode("utf-8")
            
            if self.service_type == "ollama":
                return self._generate_with_image_ollama(prompt, image_data, max_tokens)
            else:
                logging.warning("Image input only supported with Ollama multimodal models")
                return self.generate_text(prompt, max_tokens)
        except Exception as e:
            logging.error(f"Error generating text with image: {e}")
            return ""
    
    def _generate_with_image_ollama(self, prompt: str, image_data: str, max_tokens: int) -> str:
        """Generate text with image using Ollama API."""
        try:
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "images": [image_data],
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                logging.error(f"Ollama API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logging.error(f"Error with Ollama API: {e}")
            return ""
    
    def is_available(self) -> bool:
        """
        Check if the local LLM service is available.
        
        Returns:
            True if available, False otherwise
        """
        try:
            if self.service_type == "ollama":
                response = requests.get(f"{self.endpoint}/api/tags", timeout=2)
                return response.status_code == 200
            elif self.service_type == "lmstudio":
                response = requests.get(f"{self.endpoint}/v1/models", timeout=2)
                return response.status_code == 200
            else:
                return False
        except:
            return False
    
    def get_name(self) -> str:
        """
        Get the name of the LLM service.
        
        Returns:
            Name of the LLM service
        """
        return f"Local {self.service_type.capitalize()} - {self.model_name}"
    
    def supports_image_input(self) -> bool:
        """
        Check if the local LLM model supports image input.
        
        Returns:
            True if image input is supported, False otherwise
        """
        # Currently only Ollama with specific models supports image input
        if self.service_type != "ollama":
            return False
        
        # List of known multimodal models in Ollama
        multimodal_models = ["llava", "bakllava", "llava-llama3", "llava-phi3", "moondream"]
        
        # Check if the model name contains any of the multimodal model identifiers
        return any(mm in self.model_name.lower() for mm in multimodal_models)
    
    @staticmethod
    def list_available_models() -> List[Dict[str, Any]]:
        """
        List available local LLM models.
        
        Returns:
            List of dictionaries with model information
        """
        models = []
        
        # Try Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                ollama_models = response.json().get("models", [])
                for model in ollama_models:
                    model_name = model.get("name", "")
                    # Check if it's a multimodal model
                    multimodal_models = ["llava", "bakllava", "llava-llama3", "llava-phi3", "moondream"]
                    supports_image = any(mm in model_name.lower() for mm in multimodal_models)
                    
                    models.append({
                        "name": f"Ollama - {model_name}",
                        "model_id": model_name,
                        "supports_image": supports_image
                    })
        except:
            pass
        
        # Try LM Studio
        try:
            response = requests.get("http://localhost:1234/v1/models", timeout=2)
            if response.status_code == 200:
                lmstudio_models = response.json().get("data", [])
                for model in lmstudio_models:
                    model_name = model.get("id", "")
                    models.append({
                        "name": f"LM Studio - {model_name}",
                        "model_id": model_name,
                        "supports_image": False  # LM Studio doesn't support image input yet
                    })
        except:
            pass
        
        return models
