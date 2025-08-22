"""
Media orchestrator module for coordinating the analysis and metadata generation process.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

from givephotobankreadymediafileslib.analysis.analyzer_image import ImageAnalyzer
from givephotobankreadymediafileslib.analysis.analyzer_video import VideoAnalyzer
from givephotobankreadymediafileslib.analysis.media_loader import MediaLoader
from givephotobankreadymediafileslib.data_loader import (
    load_categories_csv,
    load_media_csv,
    save_media_csv,
    update_media_record,
)
from givephotobankreadymediafileslib.metadata.online_llm_generator import OnlineLLMMetadataGenerator


class MediaOrchestrator:
    """Class for orchestrating the analysis and metadata generation process."""

    def __init__(
        self, media_csv_path: str, categories_csv_path: str, training_data_dir: str, **generator_kwargs: Any
    ) -> None:
        """
        Initialize the media orchestrator.

        :param media_csv_path: Path to the CSV file with media records
        :type media_csv_path: str
        :param categories_csv_path: Path to the CSV file with photobank categories
        :type categories_csv_path: str
        :param training_data_dir: Directory for storing training data
        :type training_data_dir: str
        :param generator_kwargs: Additional arguments for the metadata generator
        :type generator_kwargs: Any
        :returns: None
        :rtype: None
        """
        self.media_csv_path = media_csv_path
        self.categories_csv_path = categories_csv_path
        self.training_data_dir = training_data_dir
        self.generator_kwargs = generator_kwargs

        # Initialize basic components
        self.media_loader = MediaLoader()
        self.image_analyzer = ImageAnalyzer()
        self.video_analyzer = VideoAnalyzer()
        # No need to initialize csv_loader anymore

        # Load data first
        self.media_data = None
        self.photobank_categories = None
        self.metadata_generator = None

        # Status flags
        self.data_loaded = False
        self.generators_initialized = False

        # Load data
        self.load_data()

        logging.info("MediaOrchestrator initialized")

    def load_data(self) -> bool:
        """
        Load necessary data from CSV files.

        :returns: True if data was loaded successfully, False otherwise
        :rtype: bool
        """
        try:
            # Load categories using file_operations_adapter
            self.photobank_categories = load_categories_csv(self.categories_csv_path)
            if not self.photobank_categories:
                logging.warning(f"No categories found in {self.categories_csv_path}")
                self.data_loaded = False
                return False

            # Load media data using file_operations_adapter
            media_df = load_media_csv(self.media_csv_path)
            if media_df.empty:
                logging.warning(f"No media records found in {self.media_csv_path}")
                self.data_loaded = False
                return False

            # Convert DataFrame to list of dictionaries
            self.media_data = media_df.to_dict("records")

            self.data_loaded = True
            logging.info(
                f"Loaded {len(self.media_data)} media records and categories for {len(self.photobank_categories)} photobanks"
            )
            return True

        except Exception as e:
            logging.error(f"Error loading data: {e}")
            self.data_loaded = False
            return False

    def initialize_generators(self) -> bool:
        """
        Initialize metadata generators and check their availability.

        :returns: True if all generators were initialized successfully, False otherwise
        :rtype: bool
        """
        if not self.data_loaded:
            logging.error("Cannot initialize generators: data not loaded")
            return False

        try:
            # Initialize metadata generator based on type
            self.metadata_generator = OnlineLLMMetadataGenerator(**self.generator_kwargs)
            # Check if API key is available
            if not self.metadata_generator.llm_client.api_key:
                logging.warning(f"API key not found for {self.generator_kwargs.get('provider', 'unknown')}")

            self.generators_initialized = True
            logging.info("Initialized online_llm generator")
            return True

        except Exception as e:
            logging.error(f"Error initializing generators: {e}")
            self.generators_initialized = False
            return False

    def process_media_file(self, file_path: str) -> dict[str, Any]:
        """
        Process a media file to generate metadata.

        :param file_path: Path to the media file
        :type file_path: str
        :returns: Dictionary with processing results
        :rtype: Dict[str, Any]
        """
        # Check if data is loaded and generators are initialized
        if not self.data_loaded:
            if not self.load_data():
                return {"error": "Failed to load necessary data"}

        if not self.generators_initialized:
            if not self.initialize_generators():
                return {"error": "Failed to initialize metadata generators"}

        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logging.error(f"File not found: {file_path}")
                return {"error": "File not found"}

            # Load media file
            media_data = self.media_loader.load_media_file(file_path)

            if media_data is None:
                logging.error(f"Failed to load media file: {file_path}")
                return {"error": "Failed to load media file"}

            # Analyze media file
            if media_data["type"] == "image":
                analysis_results = self.image_analyzer.analyze_image(media_data["data"])
            elif media_data["type"] == "video":
                # For videos, analyze the first frame
                analysis_results = self.video_analyzer.analyze_video(file_path, frame_count=1, start_time=0)
                # Use the first frame's analysis
                if analysis_results and "frames" in analysis_results and analysis_results["frames"]:
                    analysis_results = analysis_results["frames"][0]["analysis"]
            else:
                logging.error(f"Unsupported media type: {media_data['type']}")
                return {"error": f"Unsupported media type: {media_data['type']}"}

            # Check if analysis was successful
            if not analysis_results or "features" not in analysis_results:
                logging.error(f"Failed to analyze media file: {file_path}")
                return {"error": "Failed to analyze media file"}

            # Generate metadata for each photobank
            metadata_results = {}

            # Extract features
            features = analysis_results["features"]

            # Generate common metadata (title, description, keywords)
            common_metadata = self.metadata_generator.generate_all_metadata(
                image_features=features, image_data=media_data["data"] if media_data["type"] == "image" else None
            )

            # Add common metadata to results
            metadata_results.update(common_metadata)

            # Generate categories for each photobank
            for photobank, categories in self.photobank_categories.items():
                if categories:
                    category = self.metadata_generator.generate_category(
                        image_features=features,
                        photobank=photobank,
                        available_categories=categories,
                        title=common_metadata.get("title"),
                        description=common_metadata.get("description"),
                        image_data=media_data["data"] if media_data["type"] == "image" else None,
                    )

                    # Add category to results
                    metadata_results[f"category_{photobank}"] = category

            # Add media information
            metadata_results["file_path"] = file_path
            metadata_results["file_name"] = os.path.basename(file_path)
            metadata_results["media_type"] = media_data["type"]

            if "width" in media_data and "height" in media_data:
                metadata_results["width"] = media_data["width"]
                metadata_results["height"] = media_data["height"]

            if "creation_time" in media_data:
                metadata_results["creation_time"] = media_data["creation_time"]

            # Save training data
            self._save_training_data(file_path, analysis_results, metadata_results)

            # Update media CSV
            self._update_media_csv(file_path, metadata_results)

            return metadata_results

        except Exception as e:
            logging.error(f"Error processing media file {file_path}: {e}")
            return {"error": str(e)}

    def _save_training_data(self, file_path: str, analysis: dict[str, Any], metadata: dict[str, Any]) -> bool:
        """
        Save training data for a processed media file.

        :param file_path: Path to the media file
        :type file_path: str
        :param analysis: Analysis results
        :type analysis: Dict[str, Any]
        :param metadata: Generated metadata
        :type metadata: Dict[str, Any]
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        try:
            # Create training data directory if it doesn't exist
            os.makedirs(self.training_data_dir, exist_ok=True)

            # Create training data
            training_data = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis,
                "metadata": metadata,
            }

            # Save to JSON file
            file_name = os.path.basename(file_path)
            file_base = os.path.splitext(file_name)[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = os.path.join(self.training_data_dir, f"{file_base}_{timestamp}.json")

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)

            logging.info(f"Saved training data to {json_path}")
            return True

        except Exception as e:
            logging.error(f"Error saving training data: {e}")
            return False

    def _update_media_csv(self, file_path: str, metadata: dict[str, Any]) -> bool:
        """
        Update the media CSV file with processed metadata.

        :param file_path: Path to the media file
        :type file_path: str
        :param metadata: Generated metadata
        :type metadata: Dict[str, Any]
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        try:
            # Load media CSV using file_operations_adapter
            df = load_media_csv(self.media_csv_path)

            # Update record using file_operations_adapter
            df = update_media_record(df, file_path, metadata)

            # Save media CSV using file_operations_adapter (with backup)
            success = save_media_csv(df, self.media_csv_path)

            return success

        except Exception as e:
            logging.error(f"Error updating media CSV: {e}")
            return False
