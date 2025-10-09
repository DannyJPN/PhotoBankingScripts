"""
AI Provider Factory.

Central factory for creating and managing AI providers.
Handles provider selection, configuration, and model management.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Type
from enum import Enum

from .ai_provider import AIProvider
from .cloud_ai import CloudAIProvider
from .local_ai import LocalAIProvider
from .neural_network import NeuralNetworkProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider


class ProviderType(Enum):
    """Types of AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    GOOGLE = "google"
    MISTRAL = "mistral"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    CUSTOM_NEURAL = "custom_neural"


class AIFactory:
    """
    Factory for creating and managing AI providers.
    
    Provides a unified interface to create providers from configuration,
    manage multiple providers, and handle model selection.
    """
    
    def __init__(self):
        """Initialize AI factory."""
        self._providers: Dict[str, AIProvider] = {}
        self._provider_configs: Dict[str, Dict[str, Any]] = {}
        
        # Register built-in providers
        self._provider_classes: Dict[ProviderType, Type[AIProvider]] = {
            ProviderType.OPENAI: OpenAIProvider,
            ProviderType.ANTHROPIC: AnthropicProvider,
        }
    
    def register_provider_class(self, provider_type: ProviderType, 
                               provider_class: Type[AIProvider]):
        """
        Register a custom provider class.
        
        Args:
            provider_type: Type identifier for the provider
            provider_class: Provider class implementing AIProvider
        """
        self._provider_classes[provider_type] = provider_class
        logging.info(f"Registered provider class: {provider_type.value}")
    
    def create_provider(self, provider_type: ProviderType, model_name: str, 
                       **kwargs) -> AIProvider:
        """
        Create AI provider instance.
        
        Args:
            provider_type: Type of provider to create
            model_name: Name of the model
            **kwargs: Provider-specific configuration
            
        Returns:
            AIProvider instance
        """
        if provider_type not in self._provider_classes:
            raise ValueError(f"Unknown provider type: {provider_type.value}")
        
        provider_class = self._provider_classes[provider_type]
        
        # Merge with environment variables and defaults
        config = self._get_provider_config(provider_type, **kwargs)
        
        try:
            provider = provider_class(model_name, **config)
            
            # Store provider reference
            provider_key = f"{provider_type.value}:{model_name}"
            self._providers[provider_key] = provider
            self._provider_configs[provider_key] = config
            
            logging.info(f"Created provider: {provider_key}")
            return provider
            
        except Exception as e:
            logging.error(f"Failed to create provider {provider_type.value}:{model_name}: {e}")
            raise
    
    def get_provider(self, provider_type: ProviderType, model_name: str) -> Optional[AIProvider]:
        """
        Get existing provider instance.
        
        Args:
            provider_type: Type of provider
            model_name: Name of the model
            
        Returns:
            AIProvider instance if exists, None otherwise
        """
        provider_key = f"{provider_type.value}:{model_name}"
        return self._providers.get(provider_key)
    
    def get_or_create_provider(self, provider_type: ProviderType, 
                              model_name: str, **kwargs) -> AIProvider:
        """
        Get existing provider or create new one.
        
        Args:
            provider_type: Type of provider
            model_name: Name of the model
            **kwargs: Configuration for new provider
            
        Returns:
            AIProvider instance
        """
        provider = self.get_provider(provider_type, model_name)
        if provider is None:
            provider = self.create_provider(provider_type, model_name, **kwargs)
        return provider
    
    def _get_provider_config(self, provider_type: ProviderType, **kwargs) -> Dict[str, Any]:
        """
        Get configuration for provider type with environment variable fallbacks.
        
        Args:
            provider_type: Type of provider
            **kwargs: Explicit configuration
            
        Returns:
            Merged configuration dictionary
        """
        config = kwargs.copy()
        
        # Add environment variable fallbacks
        if provider_type == ProviderType.OPENAI:
            config.setdefault('api_key', os.getenv('OPENAI_API_KEY'))
            config.setdefault('organization', os.getenv('OPENAI_ORG_ID'))
            config.setdefault('project', os.getenv('OPENAI_PROJECT_ID'))
            
        elif provider_type == ProviderType.ANTHROPIC:
            config.setdefault('api_key', os.getenv('ANTHROPIC_API_KEY'))
            
        elif provider_type == ProviderType.GOOGLE:
            config.setdefault('api_key', os.getenv('GOOGLE_API_KEY'))
            
        elif provider_type == ProviderType.MISTRAL:
            config.setdefault('api_key', os.getenv('MISTRAL_API_KEY'))
        
        # Remove None values
        config = {k: v for k, v in config.items() if v is not None}
        
        return config
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """
        List all created providers.
        
        Returns:
            List of provider information dictionaries
        """
        providers_info = []
        
        for key, provider in self._providers.items():
            info = provider.get_model_info()
            info['key'] = key
            providers_info.append(info)
        
        return providers_info
    
    def create_from_config(self, config: Dict[str, Any]) -> AIProvider:
        """
        Create provider from configuration dictionary.
        
        Args:
            config: Configuration with 'provider_type', 'model_name', and other params
            
        Returns:
            AIProvider instance
        """
        provider_type_str = config.pop('provider_type')
        model_name = config.pop('model_name')
        
        try:
            provider_type = ProviderType(provider_type_str)
        except ValueError:
            raise ValueError(f"Unknown provider type in config: {provider_type_str}")
        
        return self.create_provider(provider_type, model_name, **config)
    
    def get_available_models(self, provider_type: ProviderType) -> List[str]:
        """
        Get list of available models for a provider type.
        
        Args:
            provider_type: Type of provider
            
        Returns:
            List of model names
        """
        # This would ideally query the actual provider APIs
        # For now, return common models based on provider type
        
        models = {
            ProviderType.OPENAI: [
                'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'
            ],
            ProviderType.ANTHROPIC: [
                'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229',
                'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'
            ],
            ProviderType.GOOGLE: [
                'gemini-pro', 'gemini-pro-vision', 'gemini-ultra'
            ],
            ProviderType.MISTRAL: [
                'mistral-large-latest', 'mistral-medium-latest', 'mistral-small-latest'
            ]
        }
        
        return models.get(provider_type, [])
    
    def create_from_model_selector(self, model_key: str, **kwargs) -> AIProvider:
        """
        Create provider from model selector key (e.g., "openai/gpt-4o-mini").
        
        Args:
            model_key: Key in format "provider/model" 
            **kwargs: Additional configuration
            
        Returns:
            AIProvider instance
        """
        if '/' not in model_key:
            raise ValueError(f"Invalid model key format: {model_key}. Expected 'provider/model'")
        
        provider_str, model_name = model_key.split('/', 1)
        
        try:
            provider_type = ProviderType(provider_str)
        except ValueError:
            raise ValueError(f"Unknown provider type: {provider_str}")
        
        return self.get_or_create_provider(provider_type, model_name, **kwargs)
    
    def cleanup(self):
        """Clean up all providers."""
        for provider in self._providers.values():
            if hasattr(provider, 'unload_model'):
                try:
                    provider.unload_model()
                except Exception as e:
                    logging.warning(f"Error unloading provider: {e}")
        
        self._providers.clear()
        self._provider_configs.clear()
        logging.info("AI factory cleanup completed")


# Global factory instance
_factory = None

def get_ai_factory() -> AIFactory:
    """Get global AI factory instance."""
    global _factory
    if _factory is None:
        _factory = AIFactory()
    return _factory

def create_provider(provider_type: ProviderType, model_name: str, **kwargs) -> AIProvider:
    """Convenience function to create provider using global factory."""
    return get_ai_factory().create_provider(provider_type, model_name, **kwargs)

def create_from_model_key(model_key: str, **kwargs) -> AIProvider:
    """Convenience function to create provider from model key."""
    return get_ai_factory().create_from_model_selector(model_key, **kwargs)