"""
System checker module for verifying system prerequisites before starting the application.
"""

import logging
import os

import pandas as pd

from givephotobankreadymediafileslib.constants import COL_FILE, COL_PATH, COL_STATUS_SUFFIX, STATUS_UNPROCESSED
from givephotobankreadymediafileslib.data_loader import (
    AIConfigLoader,
    get_system_info,
)


class SystemChecker:
    """Class for checking system prerequisites."""

    def __init__(self):
        """Initialize the system checker."""
        # No need to initialize csv_loader anymore
        self.ai_config_loader = AIConfigLoader()
        self.errors = []
        self.warnings = []
        self.available_models = {}

        # Load AI configuration
        self.ai_config = self.ai_config_loader.load_config()

    def check_file_exists(self, file_path: str, file_type: str) -> bool:
        """
        Check if a file exists.

        Args:
            file_path: Path to the file
            file_type: Type of file (for error message)

        Returns:
            True if the file exists, False otherwise
        """
        if not os.path.exists(file_path):
            self.errors.append(f"{file_type} file not found: {file_path}")
            return False

        logging.info(f"{file_type} file exists: {file_path}")
        return True

    def check_media_csv_content(self, media_df: pd.DataFrame) -> bool:
        """
        Check if media CSV contains valid data.

        Args:
            media_df: DataFrame containing media data

        Returns:
            True if the content is valid, False otherwise
        """
        # Check if media CSV has required columns
        required_columns = [COL_FILE, COL_PATH]
        missing_columns = [col for col in required_columns if col not in media_df.columns]

        if missing_columns:
            self.errors.append(f"Media CSV file missing required columns: {missing_columns}")
            return False

        logging.info(f"Media CSV file has all required columns and {len(media_df)} records")
        return True

    def check_categories_csv_content(self, categories_dict: dict[str, list[str]]) -> bool:
        """
        Check if categories CSV contains valid data.

        Args:
            categories_dict: Dictionary mapping photobank names to lists of categories

        Returns:
            True if the content is valid, False otherwise
        """
        # Check if categories dictionary has any photobanks
        if not categories_dict:
            self.warnings.append("Categories CSV file does not contain any photobank category columns")
            # This is just a warning, not an error
        else:
            logging.info(
                f"Categories CSV file contains {sum(len(cats) for cats in categories_dict.values())} categories across {len(categories_dict)} photobanks"
            )

        return True

    def check_unprocessed_files(self, media_df: pd.DataFrame) -> bool:
        """
        Check if there is at least one unprocessed file in the media CSV.

        Args:
            media_df: DataFrame containing media data

        Returns:
            True if there is at least one unprocessed file, False otherwise
        """
        try:
            # Check for status columns
            status_columns = [col for col in media_df.columns if col.lower().endswith(COL_STATUS_SUFFIX)]

            # Rychlá kontrola, zda existuje alespoň jeden nezpracovaný soubor
            if not status_columns:
                # Pokud nejsou žádné status sloupce, považujeme všechny soubory za nezpracované
                # Zkontrolujeme, zda existuje alespoň jeden soubor
                for file_path in media_df[COL_PATH]:
                    if os.path.exists(file_path):
                        logging.info(f"Found at least one unprocessed file: {file_path}")
                        return True
            else:
                # Kontrola každého status sloupce
                for status_col in status_columns:
                    # Získáme soubory s nezpracovaným statusem
                    mask = media_df[status_col] == STATUS_UNPROCESSED
                    if mask.any():
                        # Zkontrolujeme, zda existuje alespoň jeden soubor
                        for file_path in media_df.loc[mask, COL_PATH]:
                            if os.path.exists(file_path):
                                logging.info(f"Found at least one unprocessed file: {file_path}")
                                return True

            # Pokud jsme nenašli žádný nezpracovaný soubor
            self.errors.append("No unprocessed media files found. Please add media files to process.")
            return False

        except Exception as e:
            self.errors.append(f"Error checking unprocessed files: {e}")
            return False

    def check_neural_networks(self, models_dir: str) -> bool:
        """
        Check if neural network models are available and download or create missing ones.

        Args:
            models_dir: Directory containing trained models

        Returns:
            True if models are available, False otherwise
        """
        try:
            logging.debug(f"Checking neural network models in directory: {models_dir}")
            # Get available neural network models
            self.available_models = self.ai_config_loader.get_available_models(models_dir)
            neural_network_models = self.available_models.get("neural_networks", [])
            logging.debug(f"Neural network models found: {neural_network_models}")

            # Get neural network models configuration
            nn_config = self.ai_config_loader.config.get("neural_networks", {})
            nn_models_config = nn_config.get("models", {})

            if not nn_models_config:
                error_msg = "No neural network models defined in configuration"
                logging.warning(error_msg)
                self.warnings.append(error_msg)
                return False

            # Group models by base type (title, description, etc.)
            model_types_by_base = {}
            for model_type in nn_models_config.keys():
                base_type = model_type.split("_")[0]  # Extract base type (title, description, etc.)
                if base_type not in model_types_by_base:
                    model_types_by_base[base_type] = []
                model_types_by_base[base_type].append(model_type)

            # Check if at least one model of each base type is available
            required_base_types = set(model_types_by_base.keys())
            missing_base_types = required_base_types - set(neural_network_models)

            if missing_base_types:
                warning_msg = f"Missing neural network models for these types: {missing_base_types}. Models will be downloaded or created."
                logging.warning(warning_msg)
                self.warnings.append(warning_msg)
            else:
                logging.debug("All required neural network model types are available")

            # Log information about available models
            for base_type in neural_network_models:
                # Find all models of this base type
                models_of_type = model_types_by_base.get(base_type, [])
                if not models_of_type:
                    continue

                # Log information about each model variant
                for model_type in models_of_type:
                    model_config = nn_models_config.get(model_type, {})
                    if not model_config:
                        continue

                    model_variant = model_config.get("type", "custom")
                    architecture = model_config.get("architecture", "Unknown")
                    description = model_config.get("description", "No description")
                    file_name = model_config.get("file_name", "Unknown")

                    if model_variant == "pretrained":
                        model_source = model_config.get("model_source", "unknown")
                        base_model = model_config.get("base_model", "unknown")
                        logging.info(
                            f"Neural network model '{model_type}': {architecture} ({model_source}/{base_model}) - {description}"
                        )
                    else:
                        logging.info(f"Neural network model '{model_type}': Custom {architecture} - {description}")

            return True

        except Exception as e:
            error_msg = f"Error checking neural networks: {e}"
            logging.error(error_msg)
            self.errors.append(error_msg)
            return False

    def check_local_llm(self) -> bool:
        """
        Check if local LLM models are available and download missing ones if possible.

        Returns:
            True if any local LLM is available, False otherwise
        """
        try:
            logging.debug("Checking local LLM models availability")
            # Get available local LLM models
            local_llm_models = self.available_models.get("local_llm", [])
            logging.debug(f"Local LLM models found in configuration: {local_llm_models}")

            # Get system information for logging
            system_info = get_system_info()
            os_name = system_info.get("os", {}).get("name", "unknown")
            ram_gb = system_info.get("ram", {}).get("total_gb", 0)
            gpu_available = system_info.get("gpu", {}).get("available", False)
            gpu_vram_gb = system_info.get("gpu", {}).get("total_vram_gb", 0)

            logging.info(
                f"System information: OS={os_name}, RAM={ram_gb}GB, GPU={gpu_available} (VRAM: {gpu_vram_gb}GB)"
            )

            if not local_llm_models:
                warning_msg = "No compatible local LLM models found for your system"
                logging.warning(warning_msg)
                self.warnings.append(warning_msg)

                # Add more specific information about why models might not be available
                if not gpu_available and ram_gb < 8:
                    self.warnings.append(
                        "Your system has limited resources (no GPU, <8GB RAM). Consider using online LLM models instead."
                    )
                elif not gpu_available:
                    self.warnings.append("No GPU detected. Some models require GPU acceleration.")
                elif gpu_vram_gb < 4:
                    self.warnings.append(f"Limited GPU VRAM ({gpu_vram_gb}GB). Some models require more VRAM.")

                return False

            # Log information about each available model
            providers_config = self.ai_config_loader.config.get("providers", {})
            for model_id in local_llm_models:
                provider, model_name = model_id.split("/", 1)
                provider_config = providers_config.get(provider, {})
                models_config = provider_config.get("models", {})
                model_config = models_config.get(model_name, {})

                if model_config:
                    description = model_config.get("description", "No description")
                    supports_image = model_config.get("supports_image", False)
                    max_tokens = model_config.get("max_tokens", "Unknown")

                    features = []
                    if supports_image:
                        features.append("supports images")

                    features_str = f" ({', '.join(features)})" if features else ""
                    logging.info(f"Local LLM model '{model_id}': {description}{features_str}, max tokens: {max_tokens}")

            return True

        except Exception as e:
            warning_msg = f"Error checking local LLM: {e}"
            logging.error(warning_msg)
            self.warnings.append(warning_msg)
            return False

    def check_online_llm(self) -> bool:
        """
        Check if online LLM models are available.

        Returns:
            True if any online LLM is available, False otherwise
        """
        try:
            logging.debug("Checking online LLM models availability")
            # Get available online LLM models
            online_llm_models = self.available_models.get("online_llm", [])
            logging.debug(f"Online LLM models found in configuration: {online_llm_models}")

            if not online_llm_models:
                warning_msg = "No online LLM models found in configuration or API keys not available"
                logging.warning(warning_msg)
                self.warnings.append(warning_msg)
                return False

            # Check if API keys are available for each provider
            for model in online_llm_models:
                provider = model.get("provider", "")
                logging.debug(f"Checking API key for provider: {provider}")
                # This is a placeholder - actual implementation would check for API keys
                # For example, you might check environment variables or configuration files

            logging.info(f"Found online LLM models: {online_llm_models}")
            return True

        except Exception as e:
            warning_msg = f"Error checking online LLM: {e}"
            logging.error(warning_msg)
            self.warnings.append(warning_msg)
            return False

    def clear_errors_and_warnings(self):
        """
        Clear previous errors and warnings.
        """
        self.errors = []
        self.warnings = []

    def log_results(self):
        """
        Log errors and warnings.
        """
        if self.errors:
            logging.error("System check failed with errors:")
            for error in self.errors:
                logging.error(f"  - {error}")

        if self.warnings:
            logging.warning("System check completed with warnings:")
            for warning in self.warnings:
                logging.warning(f"  - {warning}")

    def get_errors(self) -> list[str]:
        """Get list of errors."""
        return self.errors

    def get_warnings(self) -> list[str]:
        """Get list of warnings."""
        return self.warnings

    def get_available_models(self) -> dict[str, list[str]]:
        """Get available models."""
        return self.available_models
