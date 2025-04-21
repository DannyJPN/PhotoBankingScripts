"""
Metadata generator module for creating titles, descriptions, keywords, and categories.
"""
import logging
import os
import json
from typing import Dict, Any, List, Optional, Tuple
import csv
from datetime import datetime

from core.constants import (
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_KEYWORDS_COUNT,
    TITLE_PROMPT,
    DESCRIPTION_PROMPT,
    KEYWORDS_PROMPT,
    CATEGORIES_PROMPT
)

class MetadataGenerator:
    """Class for generating metadata for media files."""
    
    def __init__(self, categories_file: str = None, training_data_dir: str = None):
        """
        Initialize the metadata generator.
        
        Args:
            categories_file: Path to the CSV file with photobank categories
            training_data_dir: Directory for storing training data
        """
        self.categories_file = categories_file
        self.training_data_dir = training_data_dir
        self.categories = self._load_categories()
        
        logging.debug("MetadataGenerator initialized")
    
    def _load_categories(self) -> Dict[str, List[str]]:
        """
        Load categories from the CSV file.
        
        Returns:
            Dictionary mapping photobank names to lists of categories
        """
        categories = {}
        
        if not self.categories_file or not os.path.exists(self.categories_file):
            logging.warning(f"Categories file not found: {self.categories_file}")
            return categories
        
        try:
            with open(self.categories_file, 'r', encoding='utf-8-sig', newline='') as csvfile:
                reader = csv.reader(csvfile)
                # First row contains photobank names
                photobanks = next(reader)
                
                # Initialize categories for each photobank
                for bank in photobanks:
                    categories[bank] = []
                
                # Read categories for each photobank
                for row in reader:
                    for i, category in enumerate(row):
                        if i < len(photobanks) and category:
                            categories[photobanks[i]].append(category)
            
            logging.info(f"Loaded categories for {len(categories)} photobanks")
            
        except Exception as e:
            logging.error(f"Error loading categories: {e}")
        
        return categories
    
    def generate_title(self, analysis: Dict[str, Any], llm_client) -> str:
        """
        Generate a title based on image/video analysis.
        
        Args:
            analysis: Analysis results from analyzer
            llm_client: LLM client for text generation
            
        Returns:
            Generated title string
        """
        # Extract relevant information from analysis
        prompt = TITLE_PROMPT
        
        # Add detected objects to the prompt
        if 'objects' in analysis and analysis['objects']:
            object_classes = set(obj['class'] for obj in analysis['objects'])
            prompt += f"\n\nThe image contains: {', '.join(object_classes)}."
        
        # Add composition information
        if 'composition' in analysis:
            comp = analysis['composition']
            brightness = "bright" if comp.get('brightness', 0) > 128 else "dark"
            contrast = "high contrast" if comp.get('contrast', 0) > 50 else "low contrast"
            prompt += f"\n\nThe image has a {brightness}, {contrast} composition."
        
        # Generate title using LLM
        try:
            title = llm_client.generate_text(prompt)
            
            # Truncate if necessary
            if title and len(title) > MAX_TITLE_LENGTH:
                title = title[:MAX_TITLE_LENGTH].rsplit(' ', 1)[0]
            
            return title or "Untitled"
            
        except Exception as e:
            logging.error(f"Error generating title: {e}")
            return "Untitled"
    
    def generate_description(self, analysis: Dict[str, Any], llm_client) -> str:
        """
        Generate a description based on image/video analysis.
        
        Args:
            analysis: Analysis results from analyzer
            llm_client: LLM client for text generation
            
        Returns:
            Generated description string
        """
        # Extract relevant information from analysis
        prompt = DESCRIPTION_PROMPT
        
        # Add detected objects to the prompt
        if 'objects' in analysis and analysis['objects']:
            object_classes = set(obj['class'] for obj in analysis['objects'])
            prompt += f"\n\nThe image contains: {', '.join(object_classes)}."
        
        # Add color information
        if 'colors' in analysis and analysis['colors']:
            top_colors = [f"{color['rgb']}" for color in analysis['colors'][:3]]
            prompt += f"\n\nDominant colors: {', '.join(top_colors)}."
        
        # Add composition information
        if 'composition' in analysis:
            comp = analysis['composition']
            brightness = "bright" if comp.get('brightness', 0) > 128 else "dark"
            contrast = "high contrast" if comp.get('contrast', 0) > 50 else "low contrast"
            prompt += f"\n\nThe image has a {brightness}, {contrast} composition."
        
        # Generate description using LLM
        try:
            description = llm_client.generate_text(prompt)
            
            # Truncate if necessary
            if description and len(description) > MAX_DESCRIPTION_LENGTH:
                description = description[:MAX_DESCRIPTION_LENGTH].rsplit(' ', 1)[0]
            
            return description or "No description available"
            
        except Exception as e:
            logging.error(f"Error generating description: {e}")
            return "No description available"
    
    def generate_keywords(self, analysis: Dict[str, Any], llm_client) -> List[str]:
        """
        Generate keywords based on image/video analysis.
        
        Args:
            analysis: Analysis results from analyzer
            llm_client: LLM client for text generation
            
        Returns:
            List of keyword strings
        """
        # Extract relevant information from analysis
        prompt = KEYWORDS_PROMPT
        
        # Add detected objects to the prompt
        if 'objects' in analysis and analysis['objects']:
            object_classes = set(obj['class'] for obj in analysis['objects'])
            prompt += f"\n\nThe image contains: {', '.join(object_classes)}."
        
        # Add color information
        if 'colors' in analysis and analysis['colors']:
            top_colors = [f"{color['rgb']}" for color in analysis['colors'][:3]]
            prompt += f"\n\nDominant colors: {', '.join(top_colors)}."
        
        # Add composition information
        if 'composition' in analysis:
            comp = analysis['composition']
            brightness = "bright" if comp.get('brightness', 0) > 128 else "dark"
            contrast = "high contrast" if comp.get('contrast', 0) > 50 else "low contrast"
            prompt += f"\n\nThe image has a {brightness}, {contrast} composition."
        
        # Generate keywords using LLM
        try:
            keywords_text = llm_client.generate_text(prompt)
            
            # Parse keywords (assuming comma-separated)
            if keywords_text:
                keywords = [kw.strip() for kw in keywords_text.split(',')]
                
                # Remove duplicates and empty strings
                keywords = [kw for kw in keywords if kw]
                keywords = list(dict.fromkeys(keywords))
                
                # Limit number of keywords
                keywords = keywords[:MAX_KEYWORDS_COUNT]
                
                return keywords
            
            return []
            
        except Exception as e:
            logging.error(f"Error generating keywords: {e}")
            return []
    
    def suggest_categories(self, analysis: Dict[str, Any], photobank: str, llm_client) -> List[str]:
        """
        Suggest categories for a specific photobank based on image/video analysis.
        
        Args:
            analysis: Analysis results from analyzer
            photobank: Name of the photobank
            llm_client: LLM client for text generation
            
        Returns:
            List of suggested category strings
        """
        # Check if we have categories for this photobank
        if photobank not in self.categories or not self.categories[photobank]:
            logging.warning(f"No categories available for photobank: {photobank}")
            return []
        
        # Extract relevant information from analysis
        bank_categories = self.categories[photobank]
        prompt = CATEGORIES_PROMPT.format(categories=", ".join(bank_categories))
        
        # Add detected objects to the prompt
        if 'objects' in analysis and analysis['objects']:
            object_classes = set(obj['class'] for obj in analysis['objects'])
            prompt += f"\n\nThe image contains: {', '.join(object_classes)}."
        
        # Generate category suggestion using LLM
        try:
            category_text = llm_client.generate_text(prompt)
            
            # Check if the suggested category is in the list
            if category_text:
                # Clean up the response
                category_text = category_text.strip()
                
                # Find the closest matching category
                for category in bank_categories:
                    if category.lower() in category_text.lower():
                        return [category]
                
                # If no exact match, return the first category that contains any word from the response
                words = set(category_text.lower().split())
                for category in bank_categories:
                    category_words = set(category.lower().split())
                    if words.intersection(category_words):
                        return [category]
            
            # Default to the first category if no match
            return [bank_categories[0]] if bank_categories else []
            
        except Exception as e:
            logging.error(f"Error suggesting categories: {e}")
            return [bank_categories[0]] if bank_categories else []
    
    def generate_all_metadata(self, analysis: Dict[str, Any], llm_client) -> Dict[str, Any]:
        """
        Generate all metadata based on image/video analysis.
        
        Args:
            analysis: Analysis results from analyzer
            llm_client: LLM client for text generation
            
        Returns:
            Dictionary with all generated metadata
        """
        metadata = {}
        
        # Generate title
        metadata['title'] = self.generate_title(analysis, llm_client)
        
        # Generate description
        metadata['description'] = self.generate_description(analysis, llm_client)
        
        # Generate keywords
        metadata['keywords'] = self.generate_keywords(analysis, llm_client)
        
        # Generate categories for each photobank
        metadata['categories'] = {}
        for photobank in self.categories:
            metadata['categories'][photobank] = self.suggest_categories(analysis, photobank, llm_client)
        
        # Add timestamp
        metadata['generation_date'] = datetime.now().isoformat()
        
        return metadata
    
    def save_training_data(self, file_path: str, analysis: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """
        Save analysis and metadata as training data.
        
        Args:
            file_path: Path to the media file
            analysis: Analysis results
            metadata: Generated metadata
            
        Returns:
            True if successful, False otherwise
        """
        if not self.training_data_dir:
            logging.warning("Training data directory not set, skipping save")
            return False
        
        try:
            # Create training data directory if it doesn't exist
            os.makedirs(self.training_data_dir, exist_ok=True)
            
            # Create a unique filename based on the original file
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            training_file = os.path.join(self.training_data_dir, f"{base_name}_{timestamp}.json")
            
            # Prepare data to save
            training_data = {
                'file_path': file_path,
                'timestamp': timestamp,
                'analysis': analysis,
                'metadata': metadata
            }
            
            # Save to JSON file
            with open(training_file, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Saved training data to {training_file}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving training data: {e}")
            return False
