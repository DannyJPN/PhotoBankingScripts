"""
Abstract AI Provider interface for all AI models and services.

This module defines the core API for AI providers supporting:
- Text-only messages
- Image-only messages  
- Mixed text+image messages
- Batch processing
- Streaming responses

Supports cloud AI (OpenAI, Anthropic), local AI models, and neural networks.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Iterator, BinaryIO
from enum import Enum
from dataclasses import dataclass, field
import base64


class MessageRole(Enum):
    """Message roles for conversation."""
    SYSTEM = "system"
    USER = "user" 
    ASSISTANT = "assistant"


class ContentType(Enum):
    """Types of content that can be included in messages."""
    TEXT = "text"
    IMAGE_URL = "image_url"
    IMAGE_BASE64 = "image_base64"
    DOCUMENT = "document"


@dataclass
class ContentBlock:
    """A block of content within a message."""
    type: ContentType
    content: Union[str, bytes]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def text(cls, text: str) -> 'ContentBlock':
        """Create a text content block."""
        return cls(ContentType.TEXT, text)
    
    @classmethod
    def image_url(cls, url: str, detail: str = "auto") -> 'ContentBlock':
        """Create an image URL content block."""
        return cls(ContentType.IMAGE_URL, url, {"detail": detail})
    
    @classmethod
    def image_base64(cls, image_data: bytes, mime_type: str = "image/jpeg") -> 'ContentBlock':
        """Create a base64 image content block."""
        encoded = base64.b64encode(image_data).decode('utf-8')
        return cls(ContentType.IMAGE_BASE64, encoded, {"mime_type": mime_type})
    
    @classmethod
    def image_file(cls, file_path: str, detail: str = "auto") -> 'ContentBlock':
        """Create an image content block from file."""
        from shared.file_operations import read_binary
        image_data = read_binary(file_path)
        
        # Determine MIME type from file extension
        if file_path.lower().endswith('.png'):
            mime_type = "image/png"
        elif file_path.lower().endswith('.gif'):
            mime_type = "image/gif"
        elif file_path.lower().endswith('.webp'):
            mime_type = "image/webp"
        else:
            mime_type = "image/jpeg"
            
        return cls.image_base64(image_data, mime_type)


@dataclass
class Message:
    """A message in the conversation."""
    role: MessageRole
    content: Union[str, List[ContentBlock]]
    
    @classmethod
    def system(cls, content: str) -> 'Message':
        """Create a system message."""
        return cls(MessageRole.SYSTEM, content)
    
    @classmethod
    def user(cls, content: Union[str, List[ContentBlock]]) -> 'Message':
        """Create a user message."""
        return cls(MessageRole.USER, content)
    
    @classmethod
    def assistant(cls, content: str) -> 'Message':
        """Create an assistant message."""
        return cls(MessageRole.ASSISTANT, content)
    
    @classmethod
    def user_text(cls, text: str) -> 'Message':
        """Create a user message with text only."""
        return cls.user(text)
    
    @classmethod
    def user_image(cls, image_path: str, prompt: str = "") -> 'Message':
        """Create a user message with image and optional text."""
        content_blocks = []
        if prompt:
            content_blocks.append(ContentBlock.text(prompt))
        content_blocks.append(ContentBlock.image_file(image_path))
        return cls.user(content_blocks)
    
    @classmethod
    def user_multimodal(cls, text: str, image_path: str) -> 'Message':
        """Create a user message with both text and image."""
        return cls.user([
            ContentBlock.text(text),
            ContentBlock.image_file(image_path)
        ])


@dataclass 
class AIResponse:
    """Response from AI provider."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    finish_reason: Optional[str] = None


@dataclass
class BatchJob:
    """Batch processing job."""
    job_id: str
    status: str
    messages_list: List[List[Message]]
    custom_ids: List[str]
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    results: List[AIResponse] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIProvider(ABC):
    """
    Abstract base class for all AI providers.
    
    Defines unified interface for:
    - Cloud AI services (OpenAI, Anthropic, Google, etc.)
    - Local AI models (Ollama, Hugging Face, etc.)
    - Neural networks (PyTorch, TensorFlow models)
    """
    
    def __init__(self, model_name: str, **kwargs):
        """Initialize the AI provider."""
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    def generate_text(self, messages: List[Message], **kwargs) -> AIResponse:
        """
        Generate text response from messages.
        
        Args:
            messages: List of conversation messages
            **kwargs: Provider-specific parameters
            
        Returns:
            AIResponse with generated text
        """
        pass
    
    @abstractmethod
    def generate_text_stream(self, messages: List[Message], **kwargs) -> Iterator[str]:
        """
        Generate streaming text response.
        
        Args:
            messages: List of conversation messages
            **kwargs: Provider-specific parameters
            
        Yields:
            Text chunks as they're generated
        """
        pass
    
    @abstractmethod
    def create_batch_job(self, messages_list: List[List[Message]], 
                        custom_ids: List[str], **kwargs) -> BatchJob:
        """
        Create a batch processing job.
        
        Args:
            messages_list: List of message conversations to process
            custom_ids: Custom identifiers for each request
            **kwargs: Provider-specific parameters
            
        Returns:
            BatchJob object with job details
        """
        pass
    
    @abstractmethod
    def get_batch_job(self, job_id: str) -> BatchJob:
        """
        Get batch job status and results.
        
        Args:
            job_id: Batch job identifier
            
        Returns:
            BatchJob with current status and results
        """
        pass
    
    @abstractmethod
    def cancel_batch_job(self, job_id: str) -> bool:
        """
        Cancel a batch job.
        
        Args:
            job_id: Batch job identifier
            
        Returns:
            True if successfully cancelled
        """
        pass
    
    def supports_images(self) -> bool:
        """Check if provider supports image inputs."""
        return True

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses."""
        return True

    def supports_batch(self) -> bool:
        """Check if provider supports batch processing."""
        return True

    def can_generate_with_inputs(self, has_image: bool = False, has_text: bool = False) -> bool:
        """
        Check if the model can generate with the available inputs.

        Args:
            has_image: Whether an image is available
            has_text: Whether text input is available

        Returns:
            True if the model can generate with these inputs
        """
        # Text-only models need text input
        if not self.supports_images():
            return has_text

        # Vision models can use either image or text
        return has_image or has_text

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "name": self.model_name,
            "supports_images": self.supports_images(),
            "supports_streaming": self.supports_streaming(),
            "supports_batch": self.supports_batch()
        }
    
    # Convenience methods for common use cases
    
    def chat(self, prompt: str, system_message: Optional[str] = None) -> str:
        """
        Simple text chat.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            
        Returns:
            AI response text
        """
        messages = []
        if system_message:
            messages.append(Message.system(system_message))
        messages.append(Message.user_text(prompt))
        
        response = self.generate_text(messages)
        return response.content
    
    def analyze_image(self, image_path: str, prompt: str = "Describe this image") -> str:
        """
        Analyze an image with optional prompt.
        
        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            
        Returns:
            AI analysis text
        """
        if not self.supports_images():
            raise NotImplementedError("This provider doesn't support image analysis")
            
        messages = [Message.user_image(image_path, prompt)]
        response = self.generate_text(messages)
        return response.content
    
    def multimodal_chat(self, text: str, image_path: str, 
                       system_message: Optional[str] = None) -> str:
        """
        Chat with both text and image input.
        
        Args:
            text: Text prompt
            image_path: Path to image file
            system_message: Optional system message
            
        Returns:
            AI response text
        """
        if not self.supports_images():
            raise NotImplementedError("This provider doesn't support multimodal input")
            
        messages = []
        if system_message:
            messages.append(Message.system(system_message))
        messages.append(Message.user_multimodal(text, image_path))
        
        response = self.generate_text(messages)
        return response.content
