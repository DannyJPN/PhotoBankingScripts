"""
Ollama local AI provider implementation.

Supports local Ollama models including vision models (LLaVA, BakLLaVA, CogVLM).
Communicates with Ollama server via REST API at http://localhost:11434.
"""

import json
import logging
import requests
import base64
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime

from .local_ai import LocalAIProvider
from .ai_provider import Message, AIResponse, BatchJob, ContentBlock, ContentType, MessageRole


class OllamaProvider(LocalAIProvider):
    """
    Ollama local AI provider.

    Supports:
    - LLaVA, BakLLaVA, CogVLM vision models
    - Llama, Mistral, and other text models
    - Text and image inputs
    - Streaming responses
    - Local inference via REST API
    """

    def __init__(self, model_name: str, **kwargs):
        """
        Initialize Ollama provider.

        Args:
            model_name: Name of Ollama model (e.g., 'llava', 'llama3.2')
            **kwargs: Additional configuration
                base_url: Ollama server URL (default: http://localhost:11434)
                timeout: Request timeout in seconds (default: 300)
                keep_alive: Model persistence duration (default: 5m)
                temperature: Sampling temperature (default: 0.7)
                top_p: Top-p sampling parameter (default: 0.9)
                top_k: Top-k sampling parameter (default: 40)
        """
        super().__init__(model_name, **kwargs)

        self.base_url = kwargs.get('base_url', 'http://localhost:11434')
        self.timeout = kwargs.get('timeout', 300)
        self.keep_alive = kwargs.get('keep_alive', '5m')

        self.temperature = kwargs.get('temperature', 0.7)
        self.top_p = kwargs.get('top_p', 0.9)
        self.top_k = kwargs.get('top_k', 40)

        self.vision_models = {
            'llava', 'llava:7b', 'llava:13b', 'llava:34b',
            'llava:7b-v1.6', 'llava:13b-v1.6', 'llava:34b-v1.6',
            'bakllava', 'bakllava:7b',
            'cogvlm', 'cogvlm:17b',
            'llama3.2-vision', 'llama3.2-vision:11b', 'llama3.2-vision:90b'
        }

        self.session = requests.Session()
        self.is_loaded = True

    def _get_api_endpoint(self, endpoint: str) -> str:
        """Get full API endpoint URL."""
        return f"{self.base_url}/api/{endpoint}"

    def _check_server_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def _convert_messages_to_ollama_format(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal messages to Ollama chat format."""
        ollama_messages = []

        for msg in messages:
            ollama_msg = {"role": msg.role.value}

            if isinstance(msg.content, str):
                ollama_msg["content"] = msg.content
            else:
                text_parts = []
                images = []

                for block in msg.content:
                    if block.type == ContentType.TEXT:
                        text_parts.append(block.content)
                    elif block.type == ContentType.IMAGE_BASE64:
                        images.append(block.content)
                    elif block.type == ContentType.IMAGE_URL:
                        logging.warning("Ollama requires base64 images, URL images not supported directly")

                ollama_msg["content"] = " ".join(text_parts) if text_parts else ""

                if images:
                    ollama_msg["images"] = images

            ollama_messages.append(ollama_msg)

        return ollama_messages

    def _prepare_generation_options(self, **kwargs) -> Dict[str, Any]:
        """Prepare options for Ollama generation."""
        options = {
            "temperature": kwargs.get('temperature', self.temperature),
            "top_p": kwargs.get('top_p', self.top_p),
            "top_k": kwargs.get('top_k', self.top_k),
        }

        if 'num_predict' in kwargs:
            options['num_predict'] = kwargs['num_predict']

        if 'stop' in kwargs:
            options['stop'] = kwargs['stop']

        return {k: v for k, v in options.items() if v is not None}

    def _load_model(self):
        """Load model - Ollama handles this automatically."""
        if not self._check_server_available():
            raise RuntimeError(
                f"Ollama server not available at {self.base_url}. "
                "Please ensure Ollama is running (ollama serve)."
            )

        logging.info(f"Connected to Ollama server at {self.base_url}")
        logging.info(f"Model {self.model_name} will be loaded on first request")

    def _unload_model(self):
        """Unload model from Ollama server."""
        try:
            self.session.post(
                self._get_api_endpoint("generate"),
                json={
                    "model": self.model_name,
                    "keep_alive": 0
                },
                timeout=5
            )
            logging.info(f"Unloaded model {self.model_name} from Ollama server")
        except Exception as e:
            logging.warning(f"Failed to unload model: {e}")

    def _generate_response(self, messages: List[Message], **kwargs) -> AIResponse:
        """Generate response using Ollama API."""
        if not self._check_server_available():
            raise RuntimeError(f"Ollama server not available at {self.base_url}")

        use_chat_api = len(messages) > 1 or any(msg.role == MessageRole.SYSTEM for msg in messages)

        if use_chat_api:
            return self._chat_completion(messages, **kwargs)
        else:
            return self._simple_generation(messages[0], **kwargs)

    def _chat_completion(self, messages: List[Message], **kwargs) -> AIResponse:
        """Use Ollama chat completion API."""
        ollama_messages = self._convert_messages_to_ollama_format(messages)
        options = self._prepare_generation_options(**kwargs)

        request_payload = {
            "model": self.model_name,
            "messages": ollama_messages,
            "stream": False,
            "options": options,
            "keep_alive": self.keep_alive
        }

        if 'format' in kwargs:
            request_payload['format'] = kwargs['format']

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(f"Ollama chat request to {self.model_name}")
            logging.debug(f"  - Messages: {len(ollama_messages)}")
            logging.debug(f"  - Options: {options}")

        try:
            response = self.session.post(
                self._get_api_endpoint("chat"),
                json=request_payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()

            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"Ollama response received")
                logging.debug(f"  - Content length: {len(result.get('message', {}).get('content', ''))}")
                logging.debug(f"  - Total duration: {result.get('total_duration', 0) / 1e9:.2f}s")

            return AIResponse(
                content=result['message']['content'],
                model=result.get('model', self.model_name),
                usage={
                    'prompt_tokens': result.get('prompt_eval_count', 0),
                    'completion_tokens': result.get('eval_count', 0),
                    'total_tokens': result.get('prompt_eval_count', 0) + result.get('eval_count', 0)
                },
                finish_reason=result.get('done_reason', 'stop'),
                metadata={
                    'total_duration': result.get('total_duration', 0),
                    'load_duration': result.get('load_duration', 0),
                    'prompt_eval_duration': result.get('prompt_eval_duration', 0),
                    'eval_duration': result.get('eval_duration', 0),
                    'created_at': result.get('created_at')
                }
            )

        except requests.exceptions.RequestException as e:
            logging.error(f"Ollama chat request failed: {e}")
            raise RuntimeError(f"Ollama API request failed: {e}")

    def _simple_generation(self, message: Message, **kwargs) -> AIResponse:
        """Use Ollama generate API for simple prompts."""
        options = self._prepare_generation_options(**kwargs)

        request_payload = {
            "model": self.model_name,
            "stream": False,
            "options": options,
            "keep_alive": self.keep_alive
        }

        if isinstance(message.content, str):
            request_payload["prompt"] = message.content
        else:
            text_parts = []
            images = []

            for block in message.content:
                if block.type == ContentType.TEXT:
                    text_parts.append(block.content)
                elif block.type == ContentType.IMAGE_BASE64:
                    images.append(block.content)

            request_payload["prompt"] = " ".join(text_parts) if text_parts else ""
            if images:
                request_payload["images"] = images

        if 'system' in kwargs:
            request_payload['system'] = kwargs['system']

        if 'format' in kwargs:
            request_payload['format'] = kwargs['format']

        try:
            response = self.session.post(
                self._get_api_endpoint("generate"),
                json=request_payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()

            return AIResponse(
                content=result['response'],
                model=result.get('model', self.model_name),
                usage={
                    'prompt_tokens': result.get('prompt_eval_count', 0),
                    'completion_tokens': result.get('eval_count', 0),
                    'total_tokens': result.get('prompt_eval_count', 0) + result.get('eval_count', 0)
                },
                finish_reason='stop',
                metadata={
                    'total_duration': result.get('total_duration', 0),
                    'load_duration': result.get('load_duration', 0),
                    'prompt_eval_duration': result.get('prompt_eval_duration', 0),
                    'eval_duration': result.get('eval_duration', 0),
                    'created_at': result.get('created_at')
                }
            )

        except requests.exceptions.RequestException as e:
            logging.error(f"Ollama generate request failed: {e}")
            raise RuntimeError(f"Ollama API request failed: {e}")

    def generate_text_stream(self, messages: List[Message], **kwargs) -> Iterator[str]:
        """Generate streaming text using Ollama API."""
        if not self._check_server_available():
            raise RuntimeError(f"Ollama server not available at {self.base_url}")

        use_chat_api = len(messages) > 1 or any(msg.role == MessageRole.SYSTEM for msg in messages)

        if use_chat_api:
            yield from self._chat_completion_stream(messages, **kwargs)
        else:
            yield from self._simple_generation_stream(messages[0], **kwargs)

    def _chat_completion_stream(self, messages: List[Message], **kwargs) -> Iterator[str]:
        """Streaming chat completion."""
        ollama_messages = self._convert_messages_to_ollama_format(messages)
        options = self._prepare_generation_options(**kwargs)

        request_payload = {
            "model": self.model_name,
            "messages": ollama_messages,
            "stream": True,
            "options": options,
            "keep_alive": self.keep_alive
        }

        if 'format' in kwargs:
            request_payload['format'] = kwargs['format']

        try:
            response = self.session.post(
                self._get_api_endpoint("chat"),
                json=request_payload,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        if content:
                            yield content

                    if chunk.get('done', False):
                        break

        except requests.exceptions.RequestException as e:
            logging.error(f"Ollama streaming chat request failed: {e}")
            raise RuntimeError(f"Ollama streaming request failed: {e}")

    def _simple_generation_stream(self, message: Message, **kwargs) -> Iterator[str]:
        """Streaming simple generation."""
        options = self._prepare_generation_options(**kwargs)

        request_payload = {
            "model": self.model_name,
            "stream": True,
            "options": options,
            "keep_alive": self.keep_alive
        }

        if isinstance(message.content, str):
            request_payload["prompt"] = message.content
        else:
            text_parts = []
            images = []

            for block in message.content:
                if block.type == ContentType.TEXT:
                    text_parts.append(block.content)
                elif block.type == ContentType.IMAGE_BASE64:
                    images.append(block.content)

            request_payload["prompt"] = " ".join(text_parts) if text_parts else ""
            if images:
                request_payload["images"] = images

        if 'system' in kwargs:
            request_payload['system'] = kwargs['system']

        if 'format' in kwargs:
            request_payload['format'] = kwargs['format']

        try:
            response = self.session.post(
                self._get_api_endpoint("generate"),
                json=request_payload,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if 'response' in chunk:
                        content = chunk['response']
                        if content:
                            yield content

                    if chunk.get('done', False):
                        break

        except requests.exceptions.RequestException as e:
            logging.error(f"Ollama streaming generate request failed: {e}")
            raise RuntimeError(f"Ollama streaming request failed: {e}")

    def supports_images(self) -> bool:
        """Check if current model supports images."""
        model_base = self.model_name.lower().split(':')[0]
        return model_base in {m.split(':')[0] for m in self.vision_models}

    def supports_streaming(self) -> bool:
        """Ollama supports streaming for all models."""
        return True

    def supports_batch(self) -> bool:
        """Ollama supports synchronous batch processing."""
        return True

    def get_available_models(self) -> List[str]:
        """Get list of models available on Ollama server."""
        if not self._check_server_available():
            logging.warning(f"Ollama server not available at {self.base_url}")
            return []

        try:
            response = self.session.get(
                self._get_api_endpoint("tags"),
                timeout=5
            )
            response.raise_for_status()

            result = response.json()
            return [model['name'] for model in result.get('models', [])]

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get available models: {e}")
            return []

    def pull_model(self, model_name: Optional[str] = None) -> bool:
        """Pull/download a model from Ollama library."""
        target_model = model_name or self.model_name

        logging.info(f"Pulling model {target_model} from Ollama library")

        try:
            response = self.session.post(
                self._get_api_endpoint("pull"),
                json={"name": target_model},
                timeout=3600,
                stream=True
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    status = json.loads(line)
                    if 'status' in status:
                        logging.info(f"Pull status: {status['status']}")

            logging.info(f"Successfully pulled model {target_model}")
            return True

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to pull model {target_model}: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Ollama model."""
        info = super().get_model_info()
        info.update({
            "type": "ollama",
            "base_url": self.base_url,
            "server_available": self._check_server_available(),
            "available_models": self.get_available_models() if self._check_server_available() else []
        })
        return info

    def __del__(self):
        """Clean up session on deletion."""
        if hasattr(self, 'session'):
            try:
                self.session.close()
            except Exception:
                pass