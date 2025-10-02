"""
AI-powered metadata generator for photobank media files.

Uses AI providers to generate titles, descriptions, keywords, and categories
for images and videos based on visual content analysis and prompts.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path

# Import shared AI module
from shared.ai_module import (
    AIProvider, Message, ContentBlock, 
    create_from_model_key, get_ai_factory, ProviderType
)
from shared.prompt_manager import get_prompt_manager


@dataclass
class MediaMetadata:
    """Generated metadata for a media file."""
    title: str
    description: str  
    keywords: List[str]
    categories: Dict[str, List[str]]  # photobank -> categories
    editorial: bool = False
    confidence_scores: Dict[str, float] = None


class MetadataGenerator:
    """
    AI-powered metadata generator for photobank submissions.
    
    Generates SEO-optimized titles, descriptions, keywords and categories
    using multimodal AI analysis of visual content.
    """
    
    def __init__(self, ai_provider: AIProvider):
        """
        Initialize metadata generator.
        
        Args:
            ai_provider: AI provider instance to use for generation
        """
        self.ai_provider = ai_provider
        self.prompt_manager = get_prompt_manager()
        
        # Load generation settings from configuration
        limits = self.prompt_manager.get_character_limits()
        self.max_title_length = limits.get('title', 100)
        self.max_description_length = limits.get('description', 200)
        self.max_keywords = limits.get('keywords_max', 50)
        
        # Photobank category mappings (loaded separately)
        self.photobank_categories: Dict[str, List[str]] = {}
    
    def set_photobank_categories(self, categories: Dict[str, List[str]]):
        """
        Set available categories for each photobank.
        
        Args:
            categories: Dict mapping photobank names to category lists
        """
        self.photobank_categories = categories
    
    def generate_title(self, image_path: str, context: Optional[str] = None) -> str:
        """
        Generate SEO-optimized title for image.
        
        Args:
            image_path: Path to image file
            context: Optional context or existing title to refine
            
        Returns:
            Generated title (max 100 characters)
        """
        # Validate input type support
        if not self.ai_provider.supports_images():
            logging.error(f"AI provider {self.ai_provider.__class__.__name__} does not support image analysis")
            return self._fallback_title(image_path)
        
        prompt = self.prompt_manager.get_title_prompt(context)
        
        try:
            response = self.ai_provider.analyze_image(image_path, prompt)
            title = self._clean_title(response)
            
            # Ensure length limit
            if len(title) > self.max_title_length:
                title = title[:self.max_title_length].rsplit(' ', 1)[0] + '...'
            
            return title
            
        except Exception as e:
            logging.error(f"Failed to generate title for {image_path}: {e}")
            return self._fallback_title(image_path)
    
    def generate_description(self, image_path: str, title: Optional[str] = None,
                           context: Optional[str] = None, editorial_data: Optional[Dict[str, str]] = None) -> str:
        """
        Generate detailed description for image.
        
        Args:
            image_path: Path to image file
            title: Optional title to reference
            context: Optional context or existing description
            editorial_data: Optional editorial metadata (city, country, date) for editorial format
            
        Returns:
            Generated description (max 200 characters, including editorial prefix if applicable)
        """
        # Validate input type support
        if not self.ai_provider.supports_images():
            logging.error(f"AI provider {self.ai_provider.__class__.__name__} does not support image analysis")
            return self._fallback_description(image_path, title, editorial_data)
        
        # Handle editorial format
        editorial_prefix = ""
        available_chars = self.max_description_length
        
        if editorial_data:
            city = editorial_data.get('city', '')
            country = editorial_data.get('country', '')
            date_str = editorial_data.get('date', '')
            
            if city and country and date_str:
                editorial_prefix = f"{city.upper()}, {country.upper()} - {date_str}: "
                available_chars = self.max_description_length - len(editorial_prefix)
                
                if available_chars <= 20:  # Need at least some space for AI content
                    logging.warning("Editorial prefix too long, using fallback")
                    return self._fallback_description(image_path, title, editorial_data)

        # For now, use existing prompt format - editorial handling is done in prefix
        prompt = self.prompt_manager.get_description_prompt(title, context)
        
        try:
            response = self.ai_provider.analyze_image(image_path, prompt)
            description = self._clean_description(response)
            
            # Ensure AI part fits in available space
            if len(description) > available_chars:
                description = description[:available_chars].rsplit(' ', 1)[0] + '...'
            
            # Combine editorial prefix with AI description
            full_description = editorial_prefix + description
            
            return full_description
            
        except Exception as e:
            logging.error(f"Failed to generate description for {image_path}: {e}")
            return self._fallback_description(image_path, title, editorial_data)
    
    def generate_keywords(self, image_path: str, title: Optional[str] = None,
                         description: Optional[str] = None, count: int = 30, is_editorial: bool = False) -> List[str]:
        """
        Generate relevant keywords for image.
        
        Args:
            image_path: Path to image file
            title: Optional title to include keywords from
            description: Optional description to include keywords from
            count: Target number of keywords (max 50)
            is_editorial: Whether this is editorial content (adds "Editorial" keyword)
            
        Returns:
            List of keywords
        """
        # Validate input type support
        if not self.ai_provider.supports_images():
            logging.error(f"AI provider {self.ai_provider.__class__.__name__} does not support image analysis")
            return self._fallback_keywords(image_path, title, description, is_editorial)
        
        count = min(count, self.max_keywords)
        prompt = self.prompt_manager.get_keywords_prompt(title, description, count)
        
        try:
            response = self.ai_provider.analyze_image(image_path, prompt)
            keywords = self._parse_keywords(response)
            
            # Add Editorial keyword if needed (at the beginning)
            if is_editorial and "Editorial" not in keywords:
                keywords.insert(0, "Editorial")
            
            # Limit to requested count
            return keywords[:count]
            
        except Exception as e:
            logging.error(f"Failed to generate keywords for {image_path}: {e}")
            return self._fallback_keywords(image_path, title, description, is_editorial)
    
    def generate_categories(self, image_path: str, title: Optional[str] = None,
                          description: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Generate appropriate categories for each photobank.
        
        Args:
            image_path: Path to image file
            title: Optional title for context
            description: Optional description for context
            
        Returns:
            Dict mapping photobank names to selected categories
        """
        if not self.photobank_categories:
            logging.warning("No photobank categories loaded")
            return {}
        
        # Validate input type support
        if not self.ai_provider.supports_images():
            logging.error(f"AI provider {self.ai_provider.__class__.__name__} does not support image analysis")
            # Return fallback categories for all photobanks
            categories = {}
            for photobank, available_categories in self.photobank_categories.items():
                if available_categories:
                    categories[photobank] = self._fallback_categories(photobank, available_categories)
            return categories
        
        categories = {}
        
        for photobank, available_categories in self.photobank_categories.items():
            if not available_categories:
                continue
                
            prompt = self.prompt_manager.get_categories_prompt(photobank, available_categories, 
                                                              title, description)
            
            try:
                response = self.ai_provider.analyze_image(image_path, prompt)
                selected = self._parse_categories(response, available_categories, photobank)
                
                if selected:
                    categories[photobank] = selected
                    
            except Exception as e:
                logging.error(f"Failed to generate categories for {photobank}: {e}")
                categories[photobank] = self._fallback_categories(photobank, available_categories)
        
        return categories
    
    def detect_editorial_content(self, image_path: str, title: Optional[str] = None,
                               description: Optional[str] = None) -> bool:
        """
        Detect if image contains editorial content (news, events, people).
        
        Args:
            image_path: Path to image file
            title: Optional title for context
            description: Optional description for context
            
        Returns:
            True if editorial content detected
        """
        # Validate input type support
        if not self.ai_provider.supports_images():
            logging.error(f"AI provider {self.ai_provider.__class__.__name__} does not support image analysis")
            return False  # Conservative fallback - assume commercial content
        
        prompt = self.prompt_manager.get_editorial_prompt(title, description)
        
        try:
            response = self.ai_provider.analyze_image(image_path, prompt)
            return self._parse_editorial_response(response)
            
        except Exception as e:
            logging.error(f"Failed to detect editorial content: {e}")
            return False
    
    def generate_all_metadata(self, image_path: str, existing_metadata: Optional[Dict[str, Any]] = None) -> MediaMetadata:
        """
        Generate complete metadata for image.
        
        Args:
            image_path: Path to image file
            existing_metadata: Optional existing metadata to refine/extend
            
        Returns:
            Complete MediaMetadata object
        """
        logging.info(f"Generating metadata for: {os.path.basename(image_path)}")
        
        # Extract existing values
        existing_title = existing_metadata.get('title') if existing_metadata else None
        existing_desc = existing_metadata.get('description') if existing_metadata else None
        existing_keywords = existing_metadata.get('keywords', []) if existing_metadata else []
        
        # Generate title first (used as context for others)
        title = self.generate_title(image_path, existing_title)
        logging.info(f"Generated title: {title}")
        
        # Generate description
        description = self.generate_description(image_path, title, existing_desc)
        logging.info(f"Generated description: {description[:50]}...")
        
        # Generate keywords
        keywords = self.generate_keywords(image_path, title, description)
        logging.info(f"Generated {len(keywords)} keywords")
        
        # Generate categories
        categories = self.generate_categories(image_path, title, description)
        logging.info(f"Generated categories for {len(categories)} photobanks")
        
        # Detect editorial content
        editorial = self.detect_editorial_content(image_path, title, description)
        if editorial:
            logging.info("Editorial content detected")
        
        return MediaMetadata(
            title=title,
            description=description,
            keywords=keywords,
            categories=categories,
            editorial=editorial
        )
    
    # Prompt generation is now handled by PromptManager
    
    # Helper methods
    
    def _get_max_categories_for_photobank(self, photobank: str) -> int:
        """Get maximum number of categories for photobank."""
        limits = self.prompt_manager.get_photobank_limits()
        return limits.get(photobank.lower().replace(' ', ''), 1)
    
    def _clean_title(self, raw_title: str) -> str:
        """Clean and format generated title."""
        title = raw_title.strip().strip('"').strip("'")
        
        # Remove common prefixes
        prefixes = ['Title:', 'Generated title:', 'Image title:']
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
        
        # Capitalize first letter
        if title and title[0].islower():
            title = title[0].upper() + title[1:]
        
        return title
    
    def _clean_description(self, raw_desc: str) -> str:
        """Clean and format generated description."""
        desc = raw_desc.strip().strip('"').strip("'")
        
        # Remove common prefixes
        prefixes = ['Description:', 'Generated description:', 'Image description:']
        for prefix in prefixes:
            if desc.startswith(prefix):
                desc = desc[len(prefix):].strip()
        
        return desc
    
    def _parse_keywords(self, raw_keywords: str) -> List[str]:
        """Parse keywords from AI response."""
        # Split by commas and clean
        keywords = []
        
        for keyword in raw_keywords.split(','):
            keyword = keyword.strip().strip('"').strip("'")
            if keyword and len(keyword) > 2:
                keywords.append(keyword)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique_keywords.append(kw)
        
        return unique_keywords
    
    def _parse_categories(self, response: str, available: List[str], 
                         photobank: str) -> List[str]:
        """Parse category selection from AI response."""
        response = response.strip()
        
        # Split by commas
        selected = []
        for cat in response.split(','):
            cat = cat.strip().strip('"').strip("'")
            
            # Find best match in available categories
            best_match = self._find_best_category_match(cat, available)
            if best_match and best_match not in selected:
                selected.append(best_match)
        
        # Limit to photobank's maximum
        max_cats = self._get_max_categories_for_photobank(photobank)
        return selected[:max_cats]
    
    def _find_best_category_match(self, target: str, available: List[str]) -> Optional[str]:
        """Find best matching category from available list."""
        target_lower = target.lower()
        
        # Exact match first
        for cat in available:
            if cat.lower() == target_lower:
                return cat
        
        # Partial match
        for cat in available:
            if target_lower in cat.lower() or cat.lower() in target_lower:
                return cat
        
        return None
    
    def _parse_editorial_response(self, response: str) -> bool:
        """Parse editorial detection response."""
        response = response.strip().upper()
        return response.startswith('YES')
    
    # Fallback methods (when AI fails)
    
    def _fallback_title(self, image_path: str) -> str:
        """Generate fallback title from filename."""
        filename = Path(image_path).stem
        # Convert filename to title case
        title = filename.replace('_', ' ').replace('-', ' ').title()
        return title[:self.max_title_length]
    
    def _fallback_description(self, image_path: str, title: Optional[str] = None, editorial_data: Optional[Dict[str, str]] = None) -> str:
        """Generate fallback description."""
        # Handle editorial format
        if editorial_data:
            city = editorial_data.get('city', '')
            country = editorial_data.get('country', '')
            date_str = editorial_data.get('date', '')
            
            if city and country and date_str:
                editorial_prefix = f"{city.upper()}, {country.upper()} - {date_str}: "
                if title:
                    return editorial_prefix + f"High-quality editorial image featuring {title.lower()}"
                else:
                    filename = Path(image_path).stem
                    return editorial_prefix + f"Editorial stock image - {filename.replace('_', ' ')}"
        
        # Standard fallback
        if title:
            return f"High-quality image featuring {title.lower()}"
        else:
            filename = Path(image_path).stem
            return f"Professional stock image - {filename.replace('_', ' ')}"
    
    def _fallback_keywords(self, image_path: str, title: Optional[str] = None,
                          description: Optional[str] = None, is_editorial: bool = False) -> List[str]:
        """Generate fallback keywords."""
        keywords = []
        
        # Add Editorial keyword if needed (at the beginning)
        if is_editorial:
            keywords.append("Editorial")
        
        # Add words from title and description
        for text in [title, description]:
            if text:
                words = text.lower().replace(',', ' ').split()
                keywords.extend([w for w in words if len(w) > 3])
        
        # Add generic keywords
        if is_editorial:
            keywords.extend(['news', 'event', 'reportage', 'journalism', 'documentary'])
        else:
            keywords.extend(['professional', 'high-quality', 'commercial', 'stock'])
        
        # Remove duplicates
        return list(dict.fromkeys(keywords))[:20]
    
    def _fallback_categories(self, photobank: str, available: List[str]) -> List[str]:
        """Select fallback categories."""
        # Return most general category
        general_terms = ['other', 'general', 'miscellaneous', 'abstract', 'business']
        
        for term in general_terms:
            for cat in available:
                if term in cat.lower():
                    return [cat]
        
        # Return first category if nothing else matches
        return [available[0]] if available else []

    def generate_metadata_for_alternative(self, image_path: str, original_title: str,
                                         original_description: str, original_keywords: List[str],
                                         effect_tag: str) -> Dict[str, Any]:
        """
        Generate modified metadata for alternative version with applied effect.

        Args:
            image_path: Path to alternative image file
            original_title: Original image title
            original_description: Original image description
            original_keywords: Original image keywords
            effect_tag: Effect tag (e.g., "_bw", "_negative", "_sharpen", "_misty", "_blurred")

        Returns:
            Dict with keys: title, description, keywords
        """
        logging.info(f"Generating metadata for alternative version with effect: {effect_tag}")

        # Load effect modifiers from prompt manager
        try:
            config = self.prompt_manager.config
            effect_config = config.get("alternative_effects", {}).get(effect_tag, {})

            if not effect_config:
                logging.warning(f"No configuration found for effect {effect_tag}, using originals")
                return {
                    "title": original_title,
                    "description": original_description,
                    "keywords": original_keywords
                }

            effect_name = effect_config.get("name", effect_tag)
            title_modifier = effect_config.get("title_modifier", "")
            description_modifier = effect_config.get("description_modifier", "")
            keywords_modifier = effect_config.get("keywords_modifier", "")

        except Exception as e:
            logging.error(f"Failed to load effect configuration: {e}")
            return {
                "title": original_title,
                "description": original_description,
                "keywords": original_keywords
            }

        # Generate modified title
        title_prompt = f"""Based on the original title, generate a modified title for a {effect_name} version.

Original title: {original_title}

Modification instructions: {title_modifier}

Return ONLY the modified title, no other text."""

        try:
            if self.ai_provider.supports_images():
                modified_title = self.ai_provider.analyze_image(image_path, title_prompt)
            else:
                modified_title = self.ai_provider.generate_text(title_prompt)

            modified_title = self._clean_title(modified_title)

            # Ensure length limit
            if len(modified_title) > self.max_title_length:
                modified_title = modified_title[:self.max_title_length].rsplit(' ', 1)[0] + '...'

        except Exception as e:
            logging.error(f"Failed to generate modified title: {e}")
            modified_title = f"{original_title} - {effect_name}"

        # Generate modified description
        description_prompt = f"""Based on the original description, generate a modified description for a {effect_name} version.

Original description: {original_description}
Modified title: {modified_title}

Modification instructions: {description_modifier}

Return ONLY the modified description, no other text."""

        try:
            if self.ai_provider.supports_images():
                modified_description = self.ai_provider.analyze_image(image_path, description_prompt)
            else:
                modified_description = self.ai_provider.generate_text(description_prompt)

            modified_description = self._clean_description(modified_description)

            # Ensure length limit
            if len(modified_description) > self.max_description_length:
                modified_description = modified_description[:self.max_description_length].rsplit(' ', 1)[0] + '...'

        except Exception as e:
            logging.error(f"Failed to generate modified description: {e}")
            modified_description = f"{original_description} Modified with {effect_name} effect."

        # Generate modified keywords
        keywords_str = ", ".join(original_keywords)
        keywords_prompt = f"""Based on the original keywords, generate modified keywords for a {effect_name} version.

Original keywords: {keywords_str}
Modified title: {modified_title}
Modified description: {modified_description}

Modification instructions: {keywords_modifier}

Return ONLY the modified keywords separated by commas, no other text."""

        try:
            if self.ai_provider.supports_images():
                modified_keywords_str = self.ai_provider.analyze_image(image_path, keywords_prompt)
            else:
                modified_keywords_str = self.ai_provider.generate_text(keywords_prompt)

            modified_keywords = self._parse_keywords(modified_keywords_str)

            # Limit to max keywords
            modified_keywords = modified_keywords[:self.max_keywords]

        except Exception as e:
            logging.error(f"Failed to generate modified keywords: {e}")
            # Fallback: add effect-specific keywords to originals
            effect_keywords = {
                "_bw": ["black-and-white", "monochrome", "grayscale"],
                "_negative": ["negative", "inverted", "reversed-colors"],
                "_sharpen": ["sharp", "sharpened", "detailed"],
                "_misty": ["misty", "foggy", "hazy"],
                "_blurred": ["blurred", "blur", "soft-focus"]
            }
            modified_keywords = effect_keywords.get(effect_tag, []) + original_keywords[:25]

        logging.info(f"Generated modified metadata - Title: {modified_title[:50]}...")

        return {
            "title": modified_title,
            "description": modified_description,
            "keywords": modified_keywords
        }


def create_metadata_generator(model_key: str, **kwargs) -> MetadataGenerator:
    """
    Create metadata generator with specified AI model.
    
    Args:
        model_key: AI model key (e.g., "openai/gpt-4o-mini")
        **kwargs: Additional AI provider configuration
        
    Returns:
        MetadataGenerator instance
    """
    ai_provider = create_from_model_key(model_key, **kwargs)
    return MetadataGenerator(ai_provider)