"""
User configuration management module.

This module handles loading and managing user-specific configuration data
from environment variables or configuration files, preventing hardcoded
personal information in source code.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Optional


class UserConfig:
    """
    Manages user-specific configuration data.

    Configuration is loaded from (in order of precedence):
    1. Environment variables (PHOTOBANK_*)
    2. User config file (~/.photobanking/user.json or user.config.json)
    3. Template config file (user.template.json)
    4. System defaults (USERNAME env var, etc.)
    """

    def __init__(self):
        """Initialize user configuration."""
        self._config: Dict[str, str] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load user configuration from available sources."""
        # First try to load from config file
        config_from_file = self._load_from_file()

        # Then overlay with environment variables (higher priority)
        config_from_env = self._load_from_environment()

        # Merge configurations (env vars take precedence)
        self._config = {**config_from_file, **config_from_env}

        # Log configuration source (without exposing actual values)
        if config_from_env:
            logging.debug("User config loaded from environment variables")
        elif config_from_file:
            logging.debug("User config loaded from configuration file")
        else:
            logging.debug("User config using system defaults")

    def _load_from_file(self) -> Dict[str, str]:
        """Load configuration from file."""
        config_paths = [
            Path.home() / '.photobanking' / 'user.json',
            Path.cwd() / 'user.config.json',
            Path(__file__).parent.parent / 'user.template.json'
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        logging.debug(f"Loaded user config from: {config_path}")
                        return self._extract_user_data(config_data)
                except (json.JSONDecodeError, IOError) as e:
                    logging.warning(f"Could not load config from {config_path}: {e}")

        return {}

    def _load_from_environment(self) -> Dict[str, str]:
        """Load configuration from environment variables."""
        config = {}

        env_mappings = {
            'username': 'PHOTOBANK_USERNAME',
            'author': 'PHOTOBANK_AUTHOR',
            'location': 'PHOTOBANK_LOCATION',
            'email': 'PHOTOBANK_EMAIL',
        }

        for key, env_var in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                config[key] = value

        return config

    def _extract_user_data(self, config_data: Dict) -> Dict[str, str]:
        """Extract user data fields from configuration."""
        user_fields = ['username', 'author', 'location', 'email']
        return {
            key: str(config_data[key])
            for key in user_fields
            if key in config_data and config_data[key]
        }

    def _get_system_defaults(self) -> Dict[str, str]:
        """Get default configuration from system environment."""
        return {
            'username': os.getenv('USERNAME', os.getenv('USER', 'Anonymous')),
            'author': 'Unknown Author',
            'location': 'Unknown Location',
            'email': '',
        }

    def get_username(self) -> str:
        """
        Get photobank username.

        Returns:
            Username for photobank submissions
        """
        return self._config.get('username') or self._get_system_defaults()['username']

    def get_author(self) -> str:
        """
        Get copyright author name.

        Returns:
            Author name for copyright notices
        """
        return self._config.get('author') or self._get_system_defaults()['author']

    def get_location(self) -> str:
        """
        Get default location.

        Returns:
            Default location for metadata
        """
        return self._config.get('location') or self._get_system_defaults()['location']

    def get_email(self) -> str:
        """
        Get user email address.

        Returns:
            Email address (may be empty string)
        """
        return self._config.get('email', '')

    def is_configured(self) -> bool:
        """
        Check if user configuration is properly set up.

        Returns:
            True if user has provided custom configuration
        """
        defaults = self._get_system_defaults()
        return (
            self._config.get('author') not in (None, defaults['author']) or
            self._config.get('location') not in (None, defaults['location'])
        )

    def get_copyright_notice(self, year: Optional[int] = None) -> str:
        """
        Generate copyright notice string.

        Args:
            year: Copyright year (defaults to current year if None)

        Returns:
            Formatted copyright notice
        """
        from datetime import datetime

        if year is None:
            year = datetime.now().year

        author = self.get_author()
        return f"{author} {year}"


# Global singleton instance
_user_config_instance: Optional[UserConfig] = None


def get_user_config() -> UserConfig:
    """
    Get global user configuration instance.

    Returns:
        UserConfig singleton instance
    """
    global _user_config_instance
    if _user_config_instance is None:
        _user_config_instance = UserConfig()
    return _user_config_instance


# Convenience functions for quick access
def get_username() -> str:
    """Get photobank username."""
    return get_user_config().get_username()


def get_author() -> str:
    """Get copyright author name."""
    return get_user_config().get_author()


def get_location() -> str:
    """Get default location."""
    return get_user_config().get_location()


def get_email() -> str:
    """Get user email."""
    return get_user_config().get_email()


def get_copyright_notice(year: Optional[int] = None) -> str:
    """Generate copyright notice."""
    return get_user_config().get_copyright_notice(year)
