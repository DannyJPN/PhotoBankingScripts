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

# Import constants
from .constants import ALTERNATIVE_EDIT_TAGS, AI_MAX_RETRY_ATTEMPTS


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
        Generate SEO-optimized title for image (original version only).

        Args:
            image_path: Path to image file
            context: Optional context or existing title to refine

        Returns:
            Title string (max 100 characters)

        Raises:
            ValueError: If AI provider doesn't support images
            RuntimeError: If all retry attempts fail
        """
        # Validate input type support
        if not self.ai_provider.supports_images():
            error_msg = f"AI provider {self.ai_provider.__class__.__name__} does not support image analysis"
            logging.error(error_msg)
            raise ValueError(error_msg)

        prompt = self.prompt_manager.get_title_prompt(context)

        import json
        from shared.ai_module import Message

        messages = [Message.user_image(image_path, prompt)]

        # Determine if provider supports response_format
        provider_name = self.ai_provider.__class__.__name__.lower()
        kwargs = {}
        if 'openai' in provider_name:
            kwargs['response_format'] = {'type': 'json_object'}

        # Retry loop
        last_exception = None
        for attempt in range(1, AI_MAX_RETRY_ATTEMPTS + 1):
            try:
                logging.debug(f"AI title generation attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS}")
                response = self.ai_provider.generate_text(messages, **kwargs)
                response_text = response.content

                # Parse JSON - expect {"original": "title"}
                titles_dict = json.loads(response_text)

                # Extract original title
                if 'original' in titles_dict:
                    title = self._clean_title(titles_dict['original'])
                    if len(title) > self.max_title_length:
                        title = title[:self.max_title_length].rsplit(' ', 1)[0] + '...'

                    logging.debug(f"Successfully generated title on attempt {attempt}")
                    return title

                # Fallback: if no 'original' key, try direct string
                raise ValueError("Response missing 'original' key")

            except Exception as e:
                last_exception = e
                logging.warning(f"Title generation attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS} failed: {e}")

        # All attempts failed
        error_msg = f"AI failed to generate title after {AI_MAX_RETRY_ATTEMPTS} attempts. Last error: {last_exception}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)
    
    def generate_description(self, image_path: str, title: Optional[str] = None,
                           context: Optional[str] = None, editorial_data: Optional[Dict[str, str]] = None) -> str:
        """
        Generate detailed description for image (original version only).

        Args:
            image_path: Path to image file
            title: Optional title to reference
            context: Optional context or existing description
            editorial_data: Optional editorial metadata (city, country, date) for editorial format

        Returns:
            Description string (max 200 characters, including editorial prefix if applicable)

        Raises:
            ValueError: If AI provider doesn't support images or editorial prefix too long
            RuntimeError: If all retry attempts fail
        """
        # Validate input type support
        if not self.ai_provider.supports_images():
            error_msg = f"AI provider {self.ai_provider.__class__.__name__} does not support image analysis"
            logging.error(error_msg)
            raise ValueError(error_msg)

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
                    error_msg = f"Editorial prefix too long ({len(editorial_prefix)} chars), leaving only {available_chars} chars for content"
                    logging.error(error_msg)
                    raise ValueError(error_msg)

        prompt = self.prompt_manager.get_description_prompt(title, context)

        import json
        from shared.ai_module import Message

        messages = [Message.user_image(image_path, prompt)]

        # Determine if provider supports response_format
        provider_name = self.ai_provider.__class__.__name__.lower()
        kwargs = {}
        if 'openai' in provider_name:
            kwargs['response_format'] = {'type': 'json_object'}

        # Retry loop
        last_exception = None
        for attempt in range(1, AI_MAX_RETRY_ATTEMPTS + 1):
            try:
                logging.debug(f"AI description generation attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS}")
                response = self.ai_provider.generate_text(messages, **kwargs)
                response_text = response.content

                # Parse JSON - expect {"original": "description"}
                descriptions_dict = json.loads(response_text)

                # Extract original description
                if 'original' in descriptions_dict:
                    description = self._clean_description(descriptions_dict['original'])
                    # Ensure AI part fits in available space and ends with complete sentence
                    if len(description) > available_chars:
                        description = self._truncate_to_sentence(description, available_chars)
                    # Add editorial prefix if needed
                    if editorial_prefix:
                        description = editorial_prefix + description

                    logging.debug(f"Successfully generated description on attempt {attempt}")
                    return description

                # Fallback: if no 'original' key
                raise ValueError("Response missing 'original' key")

            except Exception as e:
                last_exception = e
                logging.warning(f"Description generation attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS} failed: {e}")

        # All attempts failed
        error_msg = f"AI failed to generate description after {AI_MAX_RETRY_ATTEMPTS} attempts. Last error: {last_exception}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)
    
    def generate_keywords(self, image_path: str, title: Optional[str] = None,
                         description: Optional[str] = None, count: int = 30, is_editorial: bool = False) -> List[str]:
        """
        Generate relevant keywords for image (original version only).

        Args:
            image_path: Path to image file
            title: Optional title to include keywords from
            description: Optional description
            count: Target number of keywords (max 50)
            is_editorial: Whether this is editorial content (adds "Editorial" keyword)

        Returns:
            List of keywords

        Raises:
            ValueError: If AI provider doesn't support images
            RuntimeError: If all retry attempts fail
        """
        # Validate input type support
        if not self.ai_provider.supports_images():
            error_msg = f"AI provider {self.ai_provider.__class__.__name__} does not support image analysis"
            logging.error(error_msg)
            raise ValueError(error_msg)

        count = min(count, self.max_keywords)

        prompt = self.prompt_manager.get_keywords_prompt(title, description, count)

        import json
        from shared.ai_module import Message

        messages = [Message.user_image(image_path, prompt)]

        # Determine if provider supports response_format
        provider_name = self.ai_provider.__class__.__name__.lower()
        kwargs = {}
        if 'openai' in provider_name:
            kwargs['response_format'] = {'type': 'json_object'}

        # Retry loop
        last_exception = None
        for attempt in range(1, AI_MAX_RETRY_ATTEMPTS + 1):
            try:
                logging.debug(f"AI keywords generation attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS}")
                response = self.ai_provider.generate_text(messages, **kwargs)
                response_text = response.content

                # Parse JSON - expect {"original": ["keyword1", "keyword2", ...]}
                keywords_dict = json.loads(response_text)

                # Extract original keywords
                if 'original' in keywords_dict:
                    keywords = keywords_dict['original']

                    # Validate and clean each keyword
                    if isinstance(keywords, list):
                        validated_keywords = []
                        for kw in keywords:
                            cleaned = self._validate_keyword(kw.strip().strip('"').strip("'"))
                            if cleaned and len(cleaned) > 2:
                                validated_keywords.append(cleaned)
                        keywords = validated_keywords
                    else:
                        # Fallback: parse as comma-separated string
                        keywords = self._parse_keywords(keywords)

                    # Remove redundant multi-word keywords
                    keywords = self._remove_duplicate_keywords(keywords)

                    # Add Editorial keyword if needed (at the beginning)
                    if is_editorial and "Editorial" not in keywords:
                        keywords.insert(0, "Editorial")

                    # Limit to requested count
                    keywords = keywords[:count]

                    logging.debug(f"Successfully generated {len(keywords)} keywords on attempt {attempt}")
                    return keywords

                # Fallback: if no 'original' key
                raise ValueError("Response missing 'original' key")

            except Exception as e:
                last_exception = e
                logging.warning(f"Keywords generation attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS} failed: {e}")

        # All attempts failed
        error_msg = f"AI failed to generate keywords after {AI_MAX_RETRY_ATTEMPTS} attempts. Last error: {last_exception}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    def generate_title_for_alternative(self, image_path: str, edit_tag: str,
                                       original_title: str) -> str:
        """
        Generate title for single alternative version.

        Args:
            image_path: Path to ORIGINAL image file (not the alternative)
            edit_tag: Edit tag like '_bw', '_negative', '_sharpen', '_misty', '_blurred'
            original_title: Title of original image for context

        Returns:
            Title string for this alternative version (max 100 characters)

        Raises:
            ValueError: If AI provider doesn't support images or edit_tag invalid
            RuntimeError: If all retry attempts fail
        """
        # Validate edit tag
        if edit_tag not in ALTERNATIVE_EDIT_TAGS:
            error_msg = f"Invalid edit_tag: {edit_tag}. Must be one of: {list(ALTERNATIVE_EDIT_TAGS.keys())}"
            logging.error(error_msg)
            raise ValueError(error_msg)

        # Validate input type support
        if not self.ai_provider.supports_images():
            error_msg = f"AI provider {self.ai_provider.__class__.__name__} does not support image analysis"
            logging.error(error_msg)
            raise ValueError(error_msg)

        prompt = self.prompt_manager.get_title_alternative_prompt(edit_tag, original_title)

        from shared.ai_module import Message

        messages = [Message.user_image(image_path, prompt)]

        # Retry loop
        last_exception = None
        for attempt in range(1, AI_MAX_RETRY_ATTEMPTS + 1):
            try:
                logging.debug(f"AI alternative title generation for {edit_tag} attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS}")
                response = self.ai_provider.generate_text(messages)
                title = response.content.strip()

                # Clean and validate
                title = self._clean_title(title)
                if len(title) > self.max_title_length:
                    title = title[:self.max_title_length].rsplit(' ', 1)[0] + '...'

                logging.debug(f"Successfully generated alternative title for {edit_tag} on attempt {attempt}")
                return title

            except Exception as e:
                last_exception = e
                logging.warning(f"Alternative title generation for {edit_tag} attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS} failed: {e}")

        # All attempts failed
        error_msg = f"AI failed to generate alternative title for {edit_tag} after {AI_MAX_RETRY_ATTEMPTS} attempts. Last error: {last_exception}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    def generate_description_for_alternative(self, image_path: str, edit_tag: str,
                                            original_title: str, original_description: str,
                                            editorial_data: Optional[Dict[str, str]] = None) -> str:
        """
        Generate description for single alternative version.

        Args:
            image_path: Path to ORIGINAL image file (not the alternative)
            edit_tag: Edit tag like '_bw', '_negative', '_sharpen', '_misty', '_blurred'
            original_title: Title of original image for context
            original_description: Description of original image for context
            editorial_data: Optional editorial metadata (city, country, date) for editorial format

        Returns:
            Description string for this alternative version (max 200 characters, including editorial prefix)

        Raises:
            ValueError: If AI provider doesn't support images, edit_tag invalid, or editorial prefix too long
            RuntimeError: If all retry attempts fail
        """
        # Validate edit tag
        if edit_tag not in ALTERNATIVE_EDIT_TAGS:
            error_msg = f"Invalid edit_tag: {edit_tag}. Must be one of: {list(ALTERNATIVE_EDIT_TAGS.keys())}"
            logging.error(error_msg)
            raise ValueError(error_msg)

        # Validate input type support
        if not self.ai_provider.supports_images():
            error_msg = f"AI provider {self.ai_provider.__class__.__name__} does not support image analysis"
            logging.error(error_msg)
            raise ValueError(error_msg)

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

                if available_chars <= 20:
                    error_msg = f"Editorial prefix too long ({len(editorial_prefix)} chars), leaving only {available_chars} chars for content"
                    logging.error(error_msg)
                    raise ValueError(error_msg)

        prompt = self.prompt_manager.get_description_alternative_prompt(
            edit_tag, original_title, original_description
        )

        from shared.ai_module import Message

        messages = [Message.user_image(image_path, prompt)]

        # Retry loop
        last_exception = None
        for attempt in range(1, AI_MAX_RETRY_ATTEMPTS + 1):
            try:
                logging.debug(f"AI alternative description generation for {edit_tag} attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS}")
                response = self.ai_provider.generate_text(messages)
                description = response.content.strip()

                # Clean and validate
                description = self._clean_description(description)
                # Ensure description fits in available space and ends with complete sentence
                if len(description) > available_chars:
                    description = self._truncate_to_sentence(description, available_chars)

                # Add editorial prefix if needed
                if editorial_prefix:
                    description = editorial_prefix + description

                logging.debug(f"Successfully generated alternative description for {edit_tag} on attempt {attempt}")
                return description

            except Exception as e:
                last_exception = e
                logging.warning(f"Alternative description generation for {edit_tag} attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS} failed: {e}")

        # All attempts failed
        error_msg = f"AI failed to generate alternative description for {edit_tag} after {AI_MAX_RETRY_ATTEMPTS} attempts. Last error: {last_exception}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    def generate_keywords_for_alternative(self, image_path: str, edit_tag: str,
                                         original_title: str, original_description: str,
                                         original_keywords: List[str], count: int = 30,
                                         is_editorial: bool = False) -> List[str]:
        """
        Generate keywords for single alternative version.

        Args:
            image_path: Path to ORIGINAL image file (not the alternative)
            edit_tag: Edit tag like '_bw', '_negative', '_sharpen', '_misty', '_blurred'
            original_title: Title of original image for context
            original_description: Description of original image for context
            original_keywords: Keywords from original image for context
            count: Target number of keywords (max 50)
            is_editorial: Whether this is editorial content (adds "Editorial" keyword)

        Returns:
            List of keywords for this alternative version

        Raises:
            ValueError: If AI provider doesn't support images or edit_tag invalid
            RuntimeError: If all retry attempts fail
        """
        # Validate edit tag
        if edit_tag not in ALTERNATIVE_EDIT_TAGS:
            error_msg = f"Invalid edit_tag: {edit_tag}. Must be one of: {list(ALTERNATIVE_EDIT_TAGS.keys())}"
            logging.error(error_msg)
            raise ValueError(error_msg)

        # Validate input type support
        if not self.ai_provider.supports_images():
            error_msg = f"AI provider {self.ai_provider.__class__.__name__} does not support image analysis"
            logging.error(error_msg)
            raise ValueError(error_msg)

        count = min(count, self.max_keywords)

        # Convert keywords list to comma-separated string
        keywords_str = ', '.join(original_keywords) if isinstance(original_keywords, list) else str(original_keywords)

        prompt = self.prompt_manager.get_keywords_alternative_prompt(
            edit_tag, original_title, original_description, keywords_str, count
        )

        from shared.ai_module import Message

        messages = [Message.user_image(image_path, prompt)]

        # Retry loop
        last_exception = None
        for attempt in range(1, AI_MAX_RETRY_ATTEMPTS + 1):
            try:
                logging.debug(f"AI alternative keywords generation for {edit_tag} attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS}")
                response = self.ai_provider.generate_text(messages)
                keywords_text = response.content.strip()

                # Parse comma-separated keywords
                keywords = self._parse_keywords(keywords_text)

                # Remove redundant multi-word keywords
                keywords = self._remove_duplicate_keywords(keywords)

                # Add Editorial keyword if needed (at the beginning)
                if is_editorial and "Editorial" not in keywords:
                    keywords.insert(0, "Editorial")

                # Limit to requested count
                keywords = keywords[:count]

                logging.debug(f"Successfully generated {len(keywords)} alternative keywords for {edit_tag} on attempt {attempt}")
                return keywords

            except Exception as e:
                last_exception = e
                logging.warning(f"Alternative keywords generation for {edit_tag} attempt {attempt}/{AI_MAX_RETRY_ATTEMPTS} failed: {e}")

        # All attempts failed
        error_msg = f"AI failed to generate alternative keywords for {edit_tag} after {AI_MAX_RETRY_ATTEMPTS} attempts. Last error: {last_exception}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

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

    def _truncate_to_sentence(self, text: str, max_length: int) -> str:
        """
        Truncate text to complete sentences within max_length.

        Finds the last sentence-ending punctuation (. ! ?) before max_length
        and truncates there. If no sentence ending found, falls back to last word.

        Args:
            text: Text to truncate
            max_length: Maximum character length

        Returns:
            Truncated text ending with complete sentence
        """
        if len(text) <= max_length:
            return text

        # Find last sentence-ending punctuation before max_length
        truncated = text[:max_length]

        # Look for sentence endings (. ! ?)
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')

        # Find the latest sentence ending
        last_sentence_end = max(last_period, last_exclamation, last_question)

        if last_sentence_end > 0:
            # Truncate at sentence ending (include the punctuation)
            return text[:last_sentence_end + 1].strip()
        else:
            # Fallback: no sentence ending found, truncate at last complete word
            logging.warning(f"No sentence ending found in description, truncating at word boundary")
            return truncated.rsplit(' ', 1)[0].strip()

    def _validate_keyword(self, keyword: str) -> str:
        """
        Validate and clean keyword according to photobank requirements.

        Keywords must be single words - no spaces allowed.
        No hyphens, special characters, or diacritics allowed.

        Args:
            keyword: Raw keyword string

        Returns:
            Cleaned keyword or empty string if invalid (multi-word or empty)
        """
        import re
        import unicodedata

        # Remove diacritics (accents) by normalizing to NFD and removing combining characters
        keyword = ''.join(c for c in unicodedata.normalize('NFD', keyword) if unicodedata.category(c) != 'Mn')

        # Remove hyphens by replacing with spaces
        keyword = keyword.replace('-', ' ')

        # Remove all characters except letters, spaces, and numbers
        keyword = re.sub(r'[^a-zA-Z0-9\s]', '', keyword)

        # Normalize whitespace (collapse multiple spaces to single space)
        keyword = ' '.join(keyword.split())

        # Trim
        keyword = keyword.strip()

        # ENFORCE SINGLE-WORD ONLY: Reject multi-word keywords
        if ' ' in keyword:
            logging.warning("Rejected multi-word keyword: '%s' (only single-word keywords allowed)", keyword)
            return ''

        return keyword

    def _parse_keywords(self, raw_keywords: str) -> List[str]:
        """Parse keywords from AI response."""
        # Split by commas and clean
        keywords = []

        for keyword in raw_keywords.split(','):
            keyword = keyword.strip().strip('"').strip("'")
            # Validate and clean keyword
            keyword = self._validate_keyword(keyword)
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

    def _remove_duplicate_keywords(self, keywords: List[str]) -> List[str]:
        """
        Remove redundant multi-word keywords that contain words already present as single keywords.

        Example: If ["blue", "pond", "blue pond"] is input, removes "blue pond"
        because both "blue" and "pond" are already present.

        This implements Shutterstock/Dreamstime anti-spam guidelines.

        Args:
            keywords: List of keywords

        Returns:
            Filtered list with redundant multi-word keywords removed
        """
        if not keywords:
            return []

        # Separate single-word and multi-word keywords
        single_word = set()
        multi_word = []

        for kw in keywords:
            kw_lower = kw.lower()
            if ' ' in kw_lower:
                multi_word.append((kw, kw_lower))
            else:
                single_word.add(kw_lower)

        # Filter multi-word keywords
        filtered_keywords = []

        # Add all single-word keywords first
        for kw in keywords:
            if ' ' not in kw.lower():
                filtered_keywords.append(kw)

        # Check each multi-word keyword
        for kw_original, kw_lower in multi_word:
            # Split into words
            words = kw_lower.split()

            # Check if ALL words are already present as single keywords
            all_words_exist = all(word in single_word for word in words)

            if not all_words_exist:
                # At least one word is NOT already present, keep this multi-word keyword
                filtered_keywords.append(kw_original)
            else:
                logging.debug(f"Removing redundant multi-word keyword: '{kw_original}' (all words already present)")

        return filtered_keywords

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