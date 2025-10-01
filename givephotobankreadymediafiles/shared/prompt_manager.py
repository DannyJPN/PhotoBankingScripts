"""
Prompt template manager for AI metadata generation.

Loads prompt templates from configuration and provides variable substitution.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path


class PromptManager:
    """
    Manager for AI prompt templates with variable substitution.
    
    Loads prompt templates from JSON configuration and provides methods
    for generating prompts with variable placeholders filled in.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize prompt manager.
        
        Args:
            config_path: Path to prompts configuration JSON file
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "prompts_config.json")
        
        self.config_path = config_path
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """Load prompts configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logging.debug(f"Loaded prompts configuration from {self.config_path}")
        except Exception as e:
            logging.error(f"Failed to load prompts config from {self.config_path}: {e}")
            self.config = {}
    
    def get_title_prompt(self, context: Optional[str] = None) -> str:
        """
        Generate title prompt with variable substitution.
        
        Args:
            context: Optional existing title to improve
            
        Returns:
            Generated prompt string
        """
        try:
            prompt_config = self.config["metadata_generation"]["title"]
            variables = prompt_config["variables"].copy()
            
            # Set context section
            context_section = ""
            if context:
                context_template = prompt_config["context_template"]
                context_section = context_template.format(context=context)
            
            # Build final prompt
            variables["context_section"] = context_section
            
            return prompt_config["template"].format(**variables)
            
        except Exception as e:
            logging.error(f"Failed to generate title prompt: {e}")
            return self._get_fallback_title_prompt(context)
    
    def get_description_prompt(self, title: Optional[str] = None, 
                             context: Optional[str] = None) -> str:
        """
        Generate description prompt with variable substitution.
        
        Args:
            title: Optional title for context
            context: Optional existing description to improve
            
        Returns:
            Generated prompt string
        """
        try:
            prompt_config = self.config["metadata_generation"]["description"]
            variables = prompt_config["variables"].copy()
            
            # Set title section
            title_section = ""
            if title:
                title_template = prompt_config["title_template"]
                title_section = title_template.format(title=title)
            
            # Set context section
            context_section = ""
            if context:
                context_template = prompt_config["context_template"]
                context_section = context_template.format(context=context)
            
            # Build final prompt
            variables["title_section"] = title_section
            variables["context_section"] = context_section
            
            return prompt_config["template"].format(**variables)
            
        except Exception as e:
            logging.error(f"Failed to generate description prompt: {e}")
            return self._get_fallback_description_prompt(title, context)
    
    def get_keywords_prompt(self, title: Optional[str] = None,
                           description: Optional[str] = None, count: int = 30) -> str:
        """
        Generate keywords prompt with variable substitution.
        
        Args:
            title: Optional title for context
            description: Optional description for context
            count: Number of keywords to generate
            
        Returns:
            Generated prompt string
        """
        try:
            prompt_config = self.config["metadata_generation"]["keywords"]
            variables = prompt_config["variables"].copy()
            variables["count"] = count
            
            # Set title section
            title_section = ""
            if title:
                title_template = prompt_config["title_template"]
                title_section = title_template.format(title=title)
            
            # Set description section
            description_section = ""
            if description:
                description_template = prompt_config["description_template"]
                description_section = description_template.format(description=description)
            
            # Build final prompt
            variables["title_section"] = title_section
            variables["description_section"] = description_section
            
            return prompt_config["template"].format(**variables)
            
        except Exception as e:
            logging.error(f"Failed to generate keywords prompt: {e}")
            return self._get_fallback_keywords_prompt(title, description, count)
    
    def get_categories_prompt(self, photobank: str, categories: List[str],
                             title: Optional[str] = None, 
                             description: Optional[str] = None) -> str:
        """
        Generate categories prompt with variable substitution.
        
        Args:
            photobank: Name of photobank
            categories: Available categories list
            title: Optional title for context
            description: Optional description for context
            
        Returns:
            Generated prompt string
        """
        try:
            prompt_config = self.config["metadata_generation"]["categories"]
            variables = prompt_config["variables"].copy()
            
            # Get max categories for this photobank
            max_categories = self._get_max_categories_for_photobank(photobank)
            variables["max_categories"] = max_categories
            variables["photobank"] = photobank
            variables["categories_list"] = ', '.join(categories)
            
            # Set grammar based on singular/plural
            variables["category_word"] = "ies" if max_categories > 1 else "y"
            variables["category_plural"] = "s" if max_categories > 1 else ""
            
            # Set title section
            title_section = ""
            if title:
                title_template = prompt_config["title_template"]
                title_section = title_template.format(title=title)
            
            # Set description section
            description_section = ""
            if description:
                description_template = prompt_config["description_template"]
                description_section = description_template.format(description=description)
            
            # Build final prompt
            variables["title_section"] = title_section
            variables["description_section"] = description_section
            
            return prompt_config["template"].format(**variables)
            
        except Exception as e:
            logging.error(f"Failed to generate categories prompt: {e}")
            return self._get_fallback_categories_prompt(photobank, categories, title, description)
    
    def get_editorial_prompt(self, title: Optional[str] = None,
                            description: Optional[str] = None) -> str:
        """
        Generate editorial detection prompt with variable substitution.
        
        Args:
            title: Optional title for context
            description: Optional description for context
            
        Returns:
            Generated prompt string
        """
        try:
            prompt_config = self.config["metadata_generation"]["editorial"]
            variables = prompt_config["variables"].copy()
            
            # Set title section
            title_section = ""
            if title:
                title_template = prompt_config["title_template"]
                title_section = title_template.format(title=title)
            
            # Set description section
            description_section = ""
            if description:
                description_template = prompt_config["description_template"]
                description_section = description_template.format(description=description)
            
            # Build final prompt
            variables["title_section"] = title_section
            variables["description_section"] = description_section
            
            return prompt_config["template"].format(**variables)
            
        except Exception as e:
            logging.error(f"Failed to generate editorial prompt: {e}")
            return self._get_fallback_editorial_prompt(title, description)
    
    def get_character_limits(self) -> Dict[str, int]:
        """
        Get character limits from configuration.
        
        Returns:
            Dictionary of character limits
        """
        try:
            return self.config.get("character_limits", {
                "title": 100,
                "description": 200,
                "keywords_max": 50
            })
        except Exception as e:
            logging.error(f"Failed to get character limits: {e}")
            return {"title": 100, "description": 200, "keywords_max": 50}
    
    def get_photobank_limits(self) -> Dict[str, int]:
        """
        Get photobank category limits from configuration.
        
        Returns:
            Dictionary of photobank category limits
        """
        try:
            return self.config.get("photobank_limits", {
                "shutterstock": 2,
                "adobestock": 1,
                "dreamstime": 3,
                "alamy": 2
            })
        except Exception as e:
            logging.error(f"Failed to get photobank limits: {e}")
            return {"shutterstock": 2, "adobestock": 1, "dreamstime": 3, "alamy": 2}
    
    def _get_max_categories_for_photobank(self, photobank: str) -> int:
        """Get maximum number of categories for photobank."""
        limits = self.get_photobank_limits()
        return limits.get(photobank.lower().replace(' ', ''), 1)
    
    # Fallback methods when config loading fails
    
    def _get_fallback_title_prompt(self, context: Optional[str] = None) -> str:
        """Fallback title prompt when config fails - minimal structure only."""
        base = "Create a title for this image.\n\n"
        if context:
            base += f"Context/existing title to improve: {context}\n\n"
        base += "Return ONLY the title, no other text."
        return base
    
    def _get_fallback_description_prompt(self, title: Optional[str] = None,
                                       context: Optional[str] = None) -> str:
        """Fallback description prompt when config fails - minimal structure only."""
        base = "Create a description for this image.\n\n"
        if title:
            base += f"Title: {title}\n"
        if context:
            base += f"Context/existing description to improve: {context}\n"
        base += "\nReturn ONLY the description, no other text."
        return base
    
    def _get_fallback_keywords_prompt(self, title: Optional[str] = None,
                                    description: Optional[str] = None, count: int = 30) -> str:
        """Fallback keywords prompt when config fails - minimal structure only."""
        base = f"Generate {count} relevant keywords for this image.\n\n"
        if title:
            base += f"Title: {title}\n"
        if description:
            base += f"Description: {description}\n"
        base += f"\nReturn ONLY {count} keywords separated by commas, no other text."
        return base
    
    def _get_fallback_categories_prompt(self, photobank: str, categories: List[str],
                                      title: Optional[str] = None,
                                      description: Optional[str] = None) -> str:
        """Fallback categories prompt when config fails - minimal structure only."""
        max_categories = self._get_max_categories_for_photobank(photobank)
        base = f"Select {max_categories} categor{'ies' if max_categories > 1 else 'y'} from: {', '.join(categories)}\n\n"
        if title:
            base += f"Title: {title}\n"
        if description:
            base += f"Description: {description}\n"
        base += f"\nReturn ONLY {max_categories} category name{'s' if max_categories > 1 else ''} separated by commas."
        return base
    
    def _get_fallback_editorial_prompt(self, title: Optional[str] = None,
                                     description: Optional[str] = None) -> str:
        """Fallback editorial prompt when config fails - minimal structure only."""
        base = "Is this image editorial content?\n\n"
        if title:
            base += f"Title: {title}\n"
        if description:
            base += f"Description: {description}\n"
        base += "\nReturn ONLY 'YES' or 'NO'."
        return base


# Global prompt manager instance
_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """
    Get global prompt manager instance.
    
    Returns:
        PromptManager instance
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager