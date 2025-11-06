"""
Shared AI module initialization.

Provides unified interface for all AI providers including:
- Cloud AI services (OpenAI, Anthropic, Google, etc.)
- Local AI models (Ollama, Hugging Face, etc.)  
- Custom neural networks (PyTorch, TensorFlow)
"""

# Core interfaces
from .ai_provider import (
    AIProvider,
    Message, 
    ContentBlock,
    AIResponse,
    BatchJob,
    MessageRole,
    ContentType
)

# Base classes
from .cloud_ai import CloudAIProvider
from .local_ai import LocalAIProvider
from .neural_network import NeuralNetworkProvider

# Specific implementations
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider

# Factory and management
from .ai_factory import (
    AIFactory,
    ProviderType,
    get_ai_factory,
    create_provider,
    create_from_model_key
)

__all__ = [
    # Core interfaces
    'AIProvider',
    'Message',
    'ContentBlock', 
    'AIResponse',
    'BatchJob',
    'MessageRole',
    'ContentType',
    
    # Base classes
    'CloudAIProvider',
    'LocalAIProvider', 
    'NeuralNetworkProvider',
    
    # Specific providers
    'OpenAIProvider',
    'AnthropicProvider',
    
    # Factory
    'AIFactory',
    'ProviderType',
    'get_ai_factory',
    'create_provider',
    'create_from_model_key'
]

__version__ = '1.0.0'