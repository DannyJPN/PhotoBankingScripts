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
    
    def get_title_prompt(self, context: Optional[str] = None,
                        user_description: Optional[str] = None) -> str:
        """
        Generate title prompt with variable substitution.

        Args:
            context: Optional existing title to improve
            user_description: Optional user input (description, commands, or notes)

        Returns:
            Generated prompt string
        """
        try:
            prompt_config = self.config["metadata_generation"]["title"]
            variables = prompt_config["variables"].copy()

            # Set user input section
            user_input_section = ""
            if user_description:
                user_input_template = prompt_config.get("user_input_template", "")
                if user_input_template:
                    user_input_section = user_input_template.format(user_description=user_description)

            # Set context section
            context_section = ""
            if context:
                context_template = prompt_config["context_template"]
                context_section = context_template.format(context=context)

            # Build final prompt
            variables["user_input_section"] = user_input_section
            variables["context_section"] = context_section

            # Support both string and array templates
            template = prompt_config["template"]
            if isinstance(template, list):
                template = "\n".join(template)

            return template.format(**variables)

        except Exception as e:
            logging.error(f"Failed to generate title prompt: {e}")
            return self._get_fallback_title_prompt(context, user_description)
    
    def get_description_prompt(self, title: Optional[str] = None,
                             context: Optional[str] = None,
                             user_description: Optional[str] = None) -> str:
        """
        Generate description prompt with variable substitution.

        Args:
            title: Optional title for context
            context: Optional existing description to improve
            user_description: Optional user input (description, commands, or notes)

        Returns:
            Generated prompt string
        """
        try:
            prompt_config = self.config["metadata_generation"]["description"]
            variables = prompt_config["variables"].copy()

            # Set user input section
            user_input_section = ""
            if user_description:
                user_input_template = prompt_config.get("user_input_template", "")
                if user_input_template:
                    user_input_section = user_input_template.format(user_description=user_description)

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
            variables["user_input_section"] = user_input_section
            variables["title_section"] = title_section
            variables["context_section"] = context_section

            # Support both string and array templates
            template = prompt_config["template"]
            if isinstance(template, list):
                template = "\n".join(template)

            return template.format(**variables)

        except Exception as e:
            logging.error(f"Failed to generate description prompt: {e}")
            return self._get_fallback_description_prompt(title, context, user_description)
    
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

            # Support both string and array templates
            template = prompt_config["template"]
            if isinstance(template, list):
                template = "\n".join(template)

            return template.format(**variables)

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
        Get character limits for metadata fields.

        Note: These are hard limits from constants.py. For soft limits used
        in AI prompts, see SOFT_* constants in givephotobankreadymediafileslib/constants.py.

        Returns:
            Dictionary of character limits (title: 80, description: 200, keywords_max: 50)
        """
        # Hard limits - single source of truth is constants.py
        # This method exists for backward compatibility
        return {"title": 80, "description": 200, "keywords_max": 50}
    
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

    def _get_fallback_title_prompt(self, context: Optional[str] = None,
                                   user_description: Optional[str] = None) -> str:
        """Fallback title prompt when config fails - minimal structure only."""
        base = "Create a title for this image.\n\n"
        if user_description:
            base += f"User input: {user_description}\n\n"
        if context:
            base += f"Context/existing title to improve: {context}\n\n"
        base += "Return ONLY the title, no other text."
        return base

    def _get_fallback_description_prompt(self, title: Optional[str] = None,
                                       context: Optional[str] = None,
                                       user_description: Optional[str] = None) -> str:
        """Fallback description prompt when config fails - minimal structure only."""
        base = "Create a description for this image.\n\n"
        if user_description:
            base += f"User input: {user_description}\n"
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

    # Alternative version generation methods

    def _get_edit_metadata(self, edit_tag: str) -> Dict[str, str]:
        """Get metadata for specific edit tag."""
        edit_info = {
            "_bw": {
                "description": "black and white",
                "hint": "black and white, monochrome, or B&W",
                "title_instructions": "Add 'black and white', 'monochrome', or 'B&W' naturally at the end of the title",
                "description_instructions": "Remove all color descriptions, add phrases about monochrome aesthetic, contrast, and tonal range",
                "keywords_instructions": "Remove color keywords, add: black and white, monochrome, grayscale, bw, contrast, tones"
            },
            "_negative": {
                "description": "color negative",
                "hint": "negative, inverted colors, or color inversion",
                "title_instructions": "Add 'negative', 'inverted colors', or 'color inversion' naturally at the end",
                "description_instructions": "Adjust color descriptions for inversion, add phrases about surreal color palette and inverted tones",
                "keywords_instructions": "Adjust color keywords for inversion, add: negative, inverted, reversed colors, surreal, artistic effect"
            },
            "_sharpen": {
                "description": "sharpened",
                "hint": "sharp, detailed, crisp, or high-detail",
                "title_instructions": "Add 'sharp', 'detailed', 'crisp', or 'high-detail' naturally at the end",
                "description_instructions": "Keep all details, add phrases about enhanced sharpness, crisp details, and clarity",
                "keywords_instructions": "Keep all keywords, add: sharp, sharpened, detailed, crisp, clarity, high definition"
            },
            "_misty": {
                "description": "misty/foggy",
                "hint": "misty, foggy, hazy, or ethereal",
                "title_instructions": "Add 'misty', 'foggy', 'hazy', or 'ethereal' naturally at the end",
                "description_instructions": "Adjust visibility descriptions, add phrases about ethereal atmosphere, fog effect, and dreamy quality",
                "keywords_instructions": "Adjust clarity keywords, add: misty, foggy, hazy, fog, mist, ethereal, dreamy, atmospheric"
            },
            "_blurred": {
                "description": "blurred",
                "hint": "blurred, soft focus, or abstract",
                "title_instructions": "Add 'blurred', 'soft focus', or 'abstract' naturally at the end",
                "description_instructions": "Adjust sharpness descriptions, add phrases about soft blur effect, abstract quality, and dreamy aesthetic",
                "keywords_instructions": "Adjust or remove sharp keywords, add: blurred, blur, soft focus, gaussian blur, abstract, dreamy"
            }
        }
        return edit_info.get(edit_tag, {})

    def get_title_alternative_prompt(self, edit_tag: str, original_title: str) -> str:
        """
        Generate title prompt for single alternative version.

        Args:
            edit_tag: Edit tag (_bw, _negative, _sharpen, _misty, _blurred)
            original_title: Original image title

        Returns:
            Generated prompt string
        """
        try:
            prompt_config = self.config["metadata_generation"]["title_alternative"]
            variables = prompt_config["variables"].copy()
            edit_meta = self._get_edit_metadata(edit_tag)

            # Set variables
            variables["original_title"] = original_title
            variables["edit_tag"] = edit_tag
            variables["edit_description"] = edit_meta.get("description", edit_tag)
            variables["edit_hint"] = edit_meta.get("hint", "")
            variables["edit_instructions"] = edit_meta.get("title_instructions", "")

            # Support both string and array templates
            template = prompt_config["template"]
            if isinstance(template, list):
                template = "\n".join(template)

            return template.format(**variables)

        except Exception as e:
            logging.error(f"Failed to generate title alternative prompt: {e}")
            return f"Create a title for the {edit_tag} version of this image.\nOriginal title: {original_title}\nReturn ONLY the new title."

    def get_description_alternative_prompt(self, edit_tag: str, original_title: str,
                                          original_description: str) -> str:
        """
        Generate description prompt for single alternative version.

        Args:
            edit_tag: Edit tag (_bw, _negative, _sharpen, _misty, _blurred)
            original_title: Original image title
            original_description: Original image description

        Returns:
            Generated prompt string
        """
        try:
            prompt_config = self.config["metadata_generation"]["description_alternative"]
            variables = prompt_config["variables"].copy()
            edit_meta = self._get_edit_metadata(edit_tag)

            # Set variables
            variables["original_title"] = original_title
            variables["original_description"] = original_description
            variables["edit_tag"] = edit_tag
            variables["edit_description"] = edit_meta.get("description", edit_tag)
            variables["edit_instructions"] = edit_meta.get("description_instructions", "")

            # Support both string and array templates
            template = prompt_config["template"]
            if isinstance(template, list):
                template = "\n".join(template)

            return template.format(**variables)

        except Exception as e:
            logging.error(f"Failed to generate description alternative prompt: {e}")
            return f"Create a description for the {edit_tag} version of this image.\nOriginal title: {original_title}\nOriginal description: {original_description}\nReturn ONLY the new description."

    def get_keywords_alternative_prompt(self, edit_tag: str, original_title: str,
                                       original_description: str, original_keywords: List[str],
                                       count: int = 30) -> str:
        """
        Generate keywords prompt for single alternative version.

        Args:
            edit_tag: Edit tag (_bw, _negative, _sharpen, _misty, _blurred)
            original_title: Original image title
            original_description: Original image description
            original_keywords: Original image keywords list
            count: Number of keywords to generate

        Returns:
            Generated prompt string
        """
        try:
            prompt_config = self.config["metadata_generation"]["keywords_alternative"]
            variables = prompt_config["variables"].copy()
            edit_meta = self._get_edit_metadata(edit_tag)

            # Format original keywords as comma-separated string
            keywords_str = ", ".join(original_keywords[:10])  # Show first 10 for context
            if len(original_keywords) > 10:
                keywords_str += f", ... ({len(original_keywords)} total)"

            # Set variables
            variables["original_title"] = original_title
            variables["original_description"] = original_description
            variables["original_keywords"] = keywords_str
            variables["edit_tag"] = edit_tag
            variables["edit_description"] = edit_meta.get("description", edit_tag)
            variables["edit_instructions"] = edit_meta.get("keywords_instructions", "")
            variables["count"] = count

            # Support both string and array templates
            template = prompt_config["template"]
            if isinstance(template, list):
                template = "\n".join(template)

            return template.format(**variables)

        except Exception as e:
            logging.error(f"Failed to generate keywords alternative prompt: {e}")
            return f"Generate {count} keywords for the {edit_tag} version of this image.\nOriginal title: {original_title}\nOriginal keywords: {', '.join(original_keywords[:5])}\nReturn ONLY comma-separated keywords."


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