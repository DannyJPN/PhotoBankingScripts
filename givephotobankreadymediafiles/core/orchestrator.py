"""
Orchestrator module for coordinating the analysis and metadata generation process.
"""
import logging
import os
import json
import csv
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from core.media_loader import MediaLoader
from core.analyzer_image import ImageAnalyzer
from core.analyzer_video import VideoAnalyzer
from core.metadata_generator import MetadataGenerator
from core.llm_client import LLMClientFactory
from core.constants import (
    COL_FILE, COL_TITLE, COL_DESCRIPTION, COL_PREP_DATE, 
    COL_WIDTH, COL_HEIGHT, COL_RESOLUTION, COL_KEYWORDS,
    COL_CATEGORIES, COL_CREATE_DATE, COL_ORIGINAL, COL_PATH,
    COL_STATUS_PREFIX, STATUS_UNPROCESSED, STATUS_PROCESSED,
    ORIGINAL_YES
)


class Orchestrator:
    """Class for orchestrating the analysis and metadata generation process."""
    
    def __init__(self, 
                 media_csv_path: str,
                 categories_csv_path: str,
                 training_data_dir: str,
                 llm_client_type: str = "local",
                 llm_model_name: str = None,
                 **llm_kwargs):
        """
        Initialize the orchestrator.
        
        Args:
            media_csv_path: Path to the CSV file with media records
            categories_csv_path: Path to the CSV file with photobank categories
            training_data_dir: Directory for storing training data
            llm_client_type: Type of LLM client to use ('local' or 'api')
            llm_model_name: Name of the LLM model to use
            **llm_kwargs: Additional arguments for the LLM client
        """
        self.media_csv_path = media_csv_path
        self.categories_csv_path = categories_csv_path
        self.training_data_dir = training_data_dir
        
        # Initialize components
        self.media_loader = MediaLoader()
        self.image_analyzer = ImageAnalyzer()
        self.video_analyzer = VideoAnalyzer()
        self.metadata_generator = MetadataGenerator(
            categories_file=categories_csv_path,
            training_data_dir=training_data_dir
        )
        
        # Initialize LLM client
        if llm_model_name:
            llm_kwargs['model_name'] = llm_model_name
        self.llm_client = LLMClientFactory.create_client(llm_client_type, **llm_kwargs)
        
        logging.debug("Orchestrator initialized")
    
    def load_media_records(self) -> List[Dict[str, str]]:
        """
        Load media records from the CSV file.
        
        Returns:
            List of media record dictionaries
        """
        try:
            from shared.file_operations import load_csv
            records = load_csv(self.media_csv_path)
            logging.info(f"Loaded {len(records)} media records from {self.media_csv_path}")
            return records
        except Exception as e:
            logging.error(f"Error loading media records: {e}")
            return []
    
    def save_media_records(self, records: List[Dict[str, str]]) -> bool:
        """
        Save media records to the CSV file.
        
        Args:
            records: List of media record dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the fieldnames from the first record
            if not records:
                logging.warning("No records to save")
                return False
            
            fieldnames = list(records[0].keys())
            
            # Write to CSV
            with open(self.media_csv_path, 'w', encoding='utf-8-sig', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
                writer.writeheader()
                for record in records:
                    writer.writerow(record)
            
            logging.info(f"Saved {len(records)} media records to {self.media_csv_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving media records: {e}")
            return False
    
    def get_unprocessed_records(self) -> List[Dict[str, str]]:
        """
        Get unprocessed media records.
        
        Returns:
            List of unprocessed media record dictionaries
        """
        records = self.load_media_records()
        
        # Filter records with Originál=ano and status=nezpracováno
        unprocessed = [
            record for record in records
            if record.get(COL_ORIGINAL) == ORIGINAL_YES and
               any(record.get(col) == STATUS_UNPROCESSED 
                   for col in record if col.startswith(COL_STATUS_PREFIX))
        ]
        
        # Sort by creation date and filename
        unprocessed.sort(key=lambda r: (r.get(COL_CREATE_DATE, ""), r.get(COL_FILE, "")))
        
        logging.info(f"Found {len(unprocessed)} unprocessed media records")
        return unprocessed
    
    def update_record(self, records: List[Dict[str, str]], record_index: int, 
                     updated_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Update a media record with new data.
        
        Args:
            records: List of all media records
            record_index: Index of the record to update
            updated_data: New data to update the record with
            
        Returns:
            Updated list of media records
        """
        if record_index < 0 or record_index >= len(records):
            logging.error(f"Invalid record index: {record_index}")
            return records
        
        # Update the record
        for key, value in updated_data.items():
            if key in records[record_index]:
                records[record_index][key] = value
        
        # Update preparation date
        records[record_index][COL_PREP_DATE] = datetime.now().strftime("%Y-%m-%d")
        
        return records
    
    def process_media_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a media file to generate metadata.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            Dictionary with generated metadata
        """
        logging.info(f"Processing media file: {file_path}")
        
        # Check if LLM client is available
        if not self.llm_client or not self.llm_client.is_available():
            logging.error("LLM client not available")
            return {}
        
        try:
            # Load the media file
            content, metadata, media_type = self.media_loader.load_media(file_path)
            
            if not content:
                logging.error(f"Failed to load media file: {file_path}")
                return {}
            
            # Analyze the media
            analysis = {}
            if media_type == "image":
                analysis = self.image_analyzer.analyze_image(content)
            elif media_type == "video":
                analysis = self.video_analyzer.analyze_video(content)
            else:
                logging.warning(f"Unsupported media type: {media_type}")
                return {}
            
            # Add basic metadata to analysis
            analysis['metadata'] = metadata
            
            # Generate metadata
            if self.llm_client.supports_image_input():
                # Use image-based generation if supported
                metadata_result = self.generate_metadata_with_image(file_path, analysis)
            else:
                # Use text-based generation
                metadata_result = self.generate_metadata_from_analysis(analysis)
            
            # Save training data
            self.metadata_generator.save_training_data(file_path, analysis, metadata_result)
            
            return metadata_result
            
        except Exception as e:
            logging.error(f"Error processing media file: {e}")
            return {}
    
    def generate_metadata_from_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate metadata based on analysis results.
        
        Args:
            analysis: Analysis results
            
        Returns:
            Dictionary with generated metadata
        """
        return self.metadata_generator.generate_all_metadata(analysis, self.llm_client)
    
    def generate_metadata_with_image(self, file_path: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate metadata using the image and analysis results.
        
        Args:
            file_path: Path to the image file
            analysis: Analysis results
            
        Returns:
            Dictionary with generated metadata
        """
        # For now, we'll use the same approach as text-based generation
        # In a more advanced implementation, we could use different prompts
        # that take advantage of the image input capability
        return self.metadata_generator.generate_all_metadata(analysis, self.llm_client)
    
    def prepare_record_data(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare record data for updating the CSV.
        
        Args:
            metadata: Generated metadata
            
        Returns:
            Dictionary with data for CSV record
        """
        record_data = {}
        
        # Basic metadata
        if 'title' in metadata:
            record_data[COL_TITLE] = metadata['title']
        
        if 'description' in metadata:
            record_data[COL_DESCRIPTION] = metadata['description']
        
        if 'keywords' in metadata:
            record_data[COL_KEYWORDS] = ", ".join(metadata['keywords'])
        
        # Categories
        if 'categories' in metadata:
            # Combine all categories into a single string
            all_categories = []
            for bank, categories in metadata['categories'].items():
                all_categories.extend(categories)
            
            # Remove duplicates and join
            unique_categories = list(dict.fromkeys(all_categories))
            record_data[COL_CATEGORIES] = ", ".join(unique_categories)
        
        # Update status for all photobanks
        if 'categories' in metadata:
            for bank in metadata['categories']:
                status_col = f"{COL_STATUS_PREFIX}{bank}"
                record_data[status_col] = STATUS_PROCESSED
        
        return record_data
    
    def process_next_record(self) -> Optional[Dict[str, Any]]:
        """
        Process the next unprocessed record.
        
        Returns:
            Processed record data or None if no records to process
        """
        # Get unprocessed records
        records = self.load_media_records()
        unprocessed = self.get_unprocessed_records()
        
        if not unprocessed:
            logging.info("No unprocessed records found")
            return None
        
        # Get the first unprocessed record
        record = unprocessed[0]
        file_path = record.get(COL_PATH)
        
        if not file_path or not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return None
        
        # Process the media file
        metadata = self.process_media_file(file_path)
        
        if not metadata:
            logging.error(f"Failed to generate metadata for {file_path}")
            return None
        
        # Prepare record data
        record_data = self.prepare_record_data(metadata)
        
        # Find the index of the record in the original list
        record_index = -1
        for i, r in enumerate(records):
            if r.get(COL_FILE) == record.get(COL_FILE) and r.get(COL_PATH) == record.get(COL_PATH):
                record_index = i
                break
        
        if record_index == -1:
            logging.error(f"Record not found in the original list: {record.get(COL_FILE)}")
            return None
        
        # Update the record
        records = self.update_record(records, record_index, record_data)
        
        # Save the updated records
        if not self.save_media_records(records):
            logging.error("Failed to save updated records")
            return None
        
        # Return the processed record
        return {
            'record': record,
            'metadata': metadata,
            'record_data': record_data
        }
    
    def get_available_llm_clients(self) -> List[Dict[str, Any]]:
        """
        Get a list of available LLM clients.
        
        Returns:
            List of dictionaries with client information
        """
        return LLMClientFactory.get_available_clients()
    
    def set_llm_client(self, client_type: str, model_name: str, **kwargs) -> bool:
        """
        Set the LLM client to use.
        
        Args:
            client_type: Type of LLM client ('local' or 'api')
            model_name: Name of the model to use
            **kwargs: Additional arguments for the LLM client
            
        Returns:
            True if successful, False otherwise
        """
        try:
            kwargs['model_name'] = model_name
            self.llm_client = LLMClientFactory.create_client(client_type, **kwargs)
            
            if not self.llm_client:
                logging.error(f"Failed to create LLM client of type {client_type} with model {model_name}")
                return False
            
            logging.info(f"Set LLM client to {self.llm_client.get_name()}")
            return True
            
        except Exception as e:
            logging.error(f"Error setting LLM client: {e}")
            return False
