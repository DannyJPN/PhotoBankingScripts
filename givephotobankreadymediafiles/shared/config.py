"""
Global configuration loader for Fotobanking scripts.
Loads from environment variables first, then from local config files.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional


class Config:
    """Configuration manager with environment variable priority."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to local config JSON file (optional)
        """
        self.config_data = {}
        self.config_file = config_file
        
        # Try to load from config file if provided
        if config_file and os.path.exists(config_file):
            self._load_config_file(config_file)
        else:
            # Load default template structure
            template_path = os.path.join(os.path.dirname(__file__), "config_template.json")
            if os.path.exists(template_path):
                self._load_config_file(template_path)
    
    def _load_config_file(self, file_path: str):
        """Load configuration from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            logging.debug(f"Loaded configuration from {file_path}")
        except Exception as e:
            logging.error(f"Failed to load config from {file_path}: {e}")
            self.config_data = {}
    
    def get_ai_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for AI provider, prioritizing environment variables.
        
        Args:
            provider: AI provider name (openai, anthropic)
            
        Returns:
            API key string or None
        """
        # First check environment variable
        if provider == "openai":
            env_key = os.environ.get("OPENAI_API_KEY")
            if env_key:
                return env_key
        elif provider == "anthropic":
            env_key = os.environ.get("ANTHROPIC_API_KEY")
            if env_key:
                return env_key
        
        # Then check config file
        try:
            provider_config = self.config_data.get("ai_providers", {}).get(provider, {})
            file_key = provider_config.get("api_key", "")
            return file_key if file_key else None
        except:
            return None
    
    def get_available_ai_models(self) -> List[Dict[str, Any]]:
        """Get list of all available AI models with their display info."""
        models = []
        
        try:
            providers = self.config_data.get("ai_providers", {})
            for provider_key, provider_info in providers.items():
                # Skip if no API key available
                if not self.get_ai_api_key(provider_key):
                    continue
                
                provider_models = provider_info.get("models", {})
                for model_key, model_info in provider_models.items():
                    models.append({
                        "key": f"{provider_key}/{model_key}",
                        "display_name": f"{provider_info.get('name', provider_key)} - {model_info.get('name', model_key)}",
                        "provider": provider_key,
                        "model": model_key,
                        "supports_images": model_info.get("supports_images", False),
                        "max_tokens": model_info.get("max_tokens", 1000),
                        "cost": model_info.get("cost_per_1k_tokens", 0.001),
                        "notes": model_info.get("notes", "")
                    })
        except Exception as e:
            logging.error(f"Error loading AI models: {e}")
        
        return models
    
    def get_ai_model_config(self, provider: str, model: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific AI model."""
        try:
            providers = self.config_data.get("ai_providers", {})
            if provider not in providers:
                return None
            
            provider_config = providers[provider]
            models = provider_config.get("models", {})
            if model not in models:
                return None
            
            model_config = models[model]
            api_key = self.get_ai_api_key(provider)
            
            if not api_key:
                return None
            
            return {
                "provider": provider,
                "model": model,
                "provider_name": provider_config.get("name", provider),
                "model_name": model_config.get("name", model),
                "api_key": api_key,
                "endpoint": provider_config.get("endpoint", ""),
                "max_tokens": model_config.get("max_tokens", 1000),
                "supports_images": model_config.get("supports_images", False),
                "cost_per_1k_tokens": model_config.get("cost_per_1k_tokens", 0.001),
                "notes": model_config.get("notes", "")
            }
        except Exception as e:
            logging.error(f"Error getting model config for {provider}/{model}: {e}")
            return None
    
    def get_default_ai_model(self) -> tuple:
        """Get default AI provider and model."""
        try:
            defaults = self.config_data.get("defaults", {})
            provider = defaults.get("ai_provider", "openai")
            model = defaults.get("ai_model", "gpt-5-mini")
            
            # Verify model is available (has API key)
            if self.get_ai_model_config(provider, model):
                return provider, model
            
            # Fall back to first available model
            available_models = self.get_available_ai_models()
            if available_models:
                first_model = available_models[0]
                return first_model["provider"], first_model["model"]
            
            return provider, model  # Return defaults even if not available
        except:
            return "openai", "gpt-5-mini"
    
    def get_gui_settings(self) -> Dict[str, Any]:
        """Get GUI configuration settings."""
        try:
            return self.config_data.get("settings", {}).get("gui", {
                "window_size": [1400, 900],
                "min_size": [1200, 800],
                "font_family": "Arial",
                "font_size": 10
            })
        except:
            return {
                "window_size": [1400, 900],
                "min_size": [1200, 800],
                "font_family": "Arial",
                "font_size": 10
            }
    
    def get_timeout_settings(self) -> Dict[str, int]:
        """Get timeout configuration settings."""
        try:
            return self.config_data.get("settings", {}).get("timeouts", {
                "default": 30,
                "ai_request": 60,
                "file_operation": 10
            })
        except:
            return {
                "default": 30,
                "ai_request": 60,
                "file_operation": 10
            }


# Global config instance
_global_config = None


def get_config(config_file: str = None) -> Config:
    """Get global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config(config_file)
    return _global_config