"""
Data loader module for loading and saving data files.
"""

import json
import logging
import os
import platform
import subprocess
import sys
from datetime import datetime
from typing import Any

import pandas as pd
import psutil
import requests
from shared.download_utils import download_file
from shared.file_operations import load_csv, save_csv_with_backup

from givephotobankreadymediafileslib.constants import (
    COL_CATEGORIES,
    COL_CREATE_DATE,
    COL_DESCRIPTION,
    COL_FILE,
    COL_HEIGHT,
    COL_KEYWORDS,
    COL_ORIGINAL,
    COL_PATH,
    COL_PREP_DATE,
    COL_RESOLUTION,
    COL_TITLE,
    COL_WIDTH,
    ORIGINAL_NO,
    ORIGINAL_YES,
)


def load_media_csv(csv_path: str) -> pd.DataFrame:
    """
    Load media CSV file using file_operations.load_csv and convert to DataFrame.

    :param csv_path: Path to the media CSV file
    :type csv_path: str
    :returns: DataFrame containing media data
    :rtype: pd.DataFrame
    """
    try:
        # Check if file exists
        if not os.path.exists(csv_path):
            logging.warning(f"Media CSV file not found: {csv_path}")
            # Create empty DataFrame with required columns
            return pd.DataFrame(
                columns=[
                    COL_FILE,
                    COL_TITLE,
                    COL_DESCRIPTION,
                    COL_PREP_DATE,
                    COL_WIDTH,
                    COL_HEIGHT,
                    COL_RESOLUTION,
                    COL_KEYWORDS,
                    COL_CATEGORIES,
                    COL_CREATE_DATE,
                    COL_ORIGINAL,
                    COL_PATH,
                ]
            )

        # Load CSV file using file_operations
        records = load_csv(csv_path)

        # Convert to DataFrame
        df = pd.DataFrame(records)

        # Check for required columns
        required_columns = [COL_FILE, COL_PATH]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            logging.warning(f"Missing required columns in media CSV: {missing_columns}")
            # Add missing columns
            for col in missing_columns:
                df[col] = ""

        logging.info(f"Loaded media CSV with {len(df)} records")
        return df

    except Exception as e:
        logging.error(f"Error loading media CSV: {e}")
        # Return empty DataFrame
        return pd.DataFrame(
            columns=[
                COL_FILE,
                COL_TITLE,
                COL_DESCRIPTION,
                COL_PREP_DATE,
                COL_WIDTH,
                COL_HEIGHT,
                COL_RESOLUTION,
                COL_KEYWORDS,
                COL_CATEGORIES,
                COL_CREATE_DATE,
                COL_ORIGINAL,
                COL_PATH,
            ]
        )


def save_media_csv(df: pd.DataFrame, csv_path: str) -> bool:
    """
    Save media CSV file using file_operations.save_csv_with_backup.

    :param df: DataFrame containing media data
    :type df: pd.DataFrame
    :param csv_path: Path to save the media CSV file
    :type csv_path: str
    :returns: True if successful, False otherwise
    :rtype: bool
    """
    try:
        # Convert DataFrame to list of dictionaries
        records = df.to_dict("records")

        # Save CSV file with backup using file_operations
        save_csv_with_backup(records, csv_path)

        logging.info(f"Saved media CSV with {len(df)} records to {csv_path}")
        return True

    except Exception as e:
        logging.error(f"Error saving media CSV: {e}")
        return False


def load_categories_csv(csv_path: str) -> dict[str, list[str]]:
    """
    Load categories CSV file using file_operations.load_csv.

    :param csv_path: Path to the categories CSV file
    :type csv_path: str
    :returns: Dictionary mapping photobank names to lists of categories
    :rtype: Dict[str, List[str]]
    """
    try:
        # Check if file exists
        if not os.path.exists(csv_path):
            logging.warning(f"Categories CSV file not found: {csv_path}")
            return {}

        # Load CSV file using file_operations
        records = load_csv(csv_path)

        if not records:
            logging.warning(f"No records found in categories CSV: {csv_path}")
            return {}

        # Convert records to DataFrame for easier processing
        df = pd.DataFrame(records)

        # V souboru kategorií jsou sloupce pojmenovány přímo názvy fotobank
        # Každý sloupec obsahuje seznam kategorií pro danou fotobanku
        photobank_columns = df.columns.tolist()

        # Create dictionary mapping photobank names to categories
        categories_dict = {}
        for photobank in photobank_columns:
            categories = df[photobank].dropna().unique().tolist()
            categories_dict[photobank] = categories

        logging.info(f"Loaded categories for {len(categories_dict)} photobanks")
        return categories_dict

    except Exception as e:
        logging.error(f"Error loading categories CSV: {e}")
        return {}


def update_media_record(df: pd.DataFrame, file_path: str, metadata: dict[str, Any]) -> pd.DataFrame:
    """
    Update a record in the media DataFrame.

    :param df: DataFrame containing media data
    :type df: pd.DataFrame
    :param file_path: Path to the media file
    :type file_path: str
    :param metadata: Dictionary containing metadata to update
    :type metadata: Dict[str, Any]
    :returns: Updated DataFrame
    :rtype: pd.DataFrame
    """
    try:
        # Check if file exists in DataFrame
        file_name = os.path.basename(file_path)
        mask = df[COL_FILE] == file_name

        if mask.any():
            # Update existing record
            for key, value in metadata.items():
                if key == "keywords" and isinstance(value, list):
                    # Join keywords with commas
                    df.loc[mask, COL_KEYWORDS] = ",".join(value)
                elif key == "category":
                    df.loc[mask, COL_CATEGORIES] = value
                elif key == "title":
                    df.loc[mask, COL_TITLE] = value
                elif key == "description":
                    df.loc[mask, COL_DESCRIPTION] = value

            # Update preparation date
            df.loc[mask, COL_PREP_DATE] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            logging.info(f"Updated record for {file_name}")
        else:
            # Create new record
            new_record = {
                COL_FILE: file_name,
                COL_PATH: file_path,
                COL_PREP_DATE: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Add metadata
            for key, value in metadata.items():
                if key == "keywords" and isinstance(value, list):
                    new_record[COL_KEYWORDS] = ",".join(value)
                elif key == "category":
                    new_record[COL_CATEGORIES] = value
                elif key == "title":
                    new_record[COL_TITLE] = value
                elif key == "description":
                    new_record[COL_DESCRIPTION] = value
                elif key == "width":
                    new_record[COL_WIDTH] = value
                elif key == "height":
                    new_record[COL_HEIGHT] = value
                elif key == "resolution":
                    new_record[COL_RESOLUTION] = value
                elif key == "create_date":
                    new_record[COL_CREATE_DATE] = value
                elif key == "original":
                    new_record[COL_ORIGINAL] = ORIGINAL_YES if value else ORIGINAL_NO

            # Add new record to DataFrame
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)

            logging.info(f"Added new record for {file_name}")

        return df

    except Exception as e:
        logging.error(f"Error updating media record: {e}")
        return df


def load_ai_config(config_path: str) -> dict[str, Any]:
    """
    Load AI configuration from JSON file.

    :param config_path: Path to the AI configuration file
    :type config_path: str
    :returns: Dictionary containing AI configuration
    :rtype: Dict[str, Any]
    """
    try:
        if not os.path.exists(config_path):
            logging.warning(f"AI configuration file not found: {config_path}")
            return {}

        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)

        logging.info(f"Loaded AI configuration from {config_path}")
        return config

    except Exception as e:
        logging.error(f"Error loading AI configuration: {e}")
        return {}


class AIConfigLoader:
    """Class for loading AI configuration and checking available models."""

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize the AI configuration loader.

        :param config_path: Path to the AI configuration file (default: config/ai_config.json)
        :type config_path: Optional[str]
        :returns: None
        :rtype: None
        """
        if config_path is None:
            # Default path is in the config directory
            self.config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                os.path.splitext(os.path.basename(sys.argv[0]))[0] + "lib",
                "config",
                "ai_config.json",
            )

        else:
            self.config_path = config_path

        self.config = None
        self.available_models = {"neural_networks": [], "local_llm": [], "online_llm": []}

    def load_config(self) -> dict[str, Any]:
        """
        Load AI configuration from the config file.

        :returns: Dictionary containing AI configuration
        :rtype: Dict[str, Any]
        """
        # Use load_ai_config function
        self.config = load_ai_config(self.config_path)
        return self.config

    def get_available_models(self, models_dir: str) -> dict[str, list[str]]:
        """
        Get available models based on configuration and filesystem.

        :param models_dir: Directory containing neural network models
        :type models_dir: str
        :returns: Dictionary containing available models by type
        :rtype: Dict[str, List[str]]
        """
        if self.config is None:
            self.load_config()

        if not self.config:
            return self.available_models

        # Check neural network models
        self._check_neural_networks(models_dir)

        # Check local LLM models
        self._check_local_llm()

        # Check online LLM models
        self._check_online_llm()

        return self.available_models

    def _check_neural_networks(self, models_dir: str) -> None:
        """
        Check available neural network models and download or create missing ones.

        :param models_dir: Directory containing neural network models
        :type models_dir: str
        :returns: None
        :rtype: None
        """
        try:
            # Check if models directory exists
            if not os.path.exists(models_dir):
                logging.warning(f"Neural network models directory not found: {models_dir}")
                os.makedirs(models_dir, exist_ok=True)
                logging.info(f"Created neural network models directory: {models_dir}")

            # Get neural network models configuration
            nn_config = self.config.get("neural_networks", {})
            nn_models_config = nn_config.get("models", {})

            if not nn_models_config:
                logging.warning("No neural network models defined in configuration")
                return

            # Check each model defined in configuration
            available_models = []
            for model_type, model_config in nn_models_config.items():
                model_file_name = model_config.get("file_name")
                model_path = os.path.join(models_dir, model_file_name)
                model_type_base = model_type.split("_")[0]  # Extract base type (title, description, etc.)

                # Check if model file exists
                if os.path.exists(model_path):
                    logging.info(f"Found neural network model for {model_type}: {model_path}")
                    available_models.append(model_type_base)
                else:
                    logging.warning(f"Neural network model for {model_type} not found: {model_path}")
                    # Try to download or create the model based on its type
                    model_type_specific = model_config.get("type", "custom")
                    if model_type_specific == "pretrained":
                        if self._download_pretrained_model(model_type, model_config, models_dir):
                            available_models.append(model_type_base)
                    else:  # custom model
                        if self._create_custom_model(model_type, model_config, models_dir):
                            available_models.append(model_type_base)

            # Add available model types to the list (deduplicate by base type)
            if available_models:
                # Remove duplicates while preserving order
                unique_models = []
                for model in available_models:
                    if model not in unique_models:
                        unique_models.append(model)
                self.available_models["neural_networks"] = unique_models
                logging.info(f"Available neural network models: {unique_models}")

        except Exception as e:
            logging.error(f"Error checking neural networks: {e}")

    def _download_pretrained_model(self, model_type: str, model_config: dict[str, Any], models_dir: str) -> bool:
        """
        Download a pretrained neural network model.

        :param model_type: Type of the model (e.g., title_pretrained)
        :type model_type: str
        :param model_config: Configuration of the model
        :type model_config: Dict[str, Any]
        :param models_dir: Directory to save the model
        :type models_dir: str
        :returns: True if the model was successfully downloaded, False otherwise
        :rtype: bool
        """
        try:
            model_file_name = model_config.get("file_name")
            model_path = os.path.join(models_dir, model_file_name)
            download_url = model_config.get("download_url")
            model_source = model_config.get("model_source", "unknown")
            base_model = model_config.get("base_model", "unknown")

            if not download_url:
                logging.error(f"No download URL provided for pretrained model {model_type}")
                return False

            # Použití generické metody pro stahování souborů
            description = f"Stahuji předtrénovaný model {model_type} ({model_source}/{base_model})"
            download_success = download_file(
                url=download_url,
                destination_path=model_path,
                description=description,
                show_progress=True,
                create_dirs=True,
                overwrite=False,
            )

            if download_success:
                # Create a training state file
                self._create_training_state_file(model_type, model_config, models_dir, is_pretrained=True)
                logging.info(f"Úspěšně stažen předtrénovaný model pro {model_type}")
                return True
            else:
                logging.error(f"Nepodařilo se stáhnout předtrénovaný model pro {model_type}")
                return False

        except Exception as e:
            logging.error(f"Error processing pretrained model for {model_type}: {e}")
            return False

    def _create_custom_model(self, model_type: str, model_config: dict[str, Any], models_dir: str) -> bool:
        """
        Create a custom neural network model from scratch.

        :param model_type: Type of the model (e.g., title_custom)
        :type model_type: str
        :param model_config: Configuration of the model
        :type model_config: Dict[str, Any]
        :param models_dir: Directory to save the model
        :type models_dir: str
        :returns: True if the model was successfully created, False otherwise
        :rtype: bool
        """
        try:
            model_file_name = model_config.get("file_name")
            model_path = os.path.join(models_dir, model_file_name)
            architecture = model_config.get("architecture", "unknown")

            logging.info(f"Creating new custom {architecture} model for {model_type}")

            # Create a placeholder model file
            # In a real implementation, this would create an actual model based on the architecture and parameters
            with open(model_path, "wb") as f:
                # Create a simple header with model type and architecture
                header = f"CUSTOM_MODEL_{model_type}_{architecture}".encode()
                f.write(header)
                # Add placeholder data
                f.write(b"\x00" * 1024)  # 1KB of zeros as placeholder

            # Create a training state file
            self._create_training_state_file(model_type, model_config, models_dir, is_pretrained=False)

            logging.info(f"Successfully created new custom model for {model_type}")
            return True

        except Exception as e:
            logging.error(f"Error creating custom model for {model_type}: {e}")
            return False

    def _create_training_state_file(
        self, model_type: str, model_config: dict[str, Any], models_dir: str, is_pretrained: bool
    ) -> None:
        """
        Create a training state file for a model.

        :param model_type: Type of the model
        :type model_type: str
        :param model_config: Configuration of the model
        :type model_config: Dict[str, Any]
        :param models_dir: Directory to save the training state file
        :type models_dir: str
        :param is_pretrained: Whether the model is pretrained or custom
        :type is_pretrained: bool
        :returns: None
        :rtype: None
        """
        training_file = model_config.get("training_file")
        if not training_file:
            return

        training_path = os.path.join(models_dir, training_file)

        # Prepare training state data
        training_state = {
            "model_type": model_type,
            "architecture": model_config.get("architecture"),
            "created_at": datetime.now().isoformat(),
            "trained": False,
            "training_iterations": 0,
            "training_data_count": 0,
        }

        # Add model-specific information
        if is_pretrained:
            training_state.update(
                {
                    "is_pretrained": True,
                    "model_source": model_config.get("model_source"),
                    "base_model": model_config.get("base_model"),
                    "fine_tuning": model_config.get("fine_tuning", {}),
                }
            )
        else:
            training_state.update(
                {
                    "is_pretrained": False,
                    "model_parameters": {
                        k: v
                        for k, v in model_config.items()
                        if k not in ["type", "description", "architecture", "file_name", "training_file"]
                    },
                }
            )

        # Save training state
        with open(training_path, "w") as f:
            json.dump(training_state, f, indent=2)

    def _check_local_llm(self) -> None:
        """
        Check available local LLM models and download missing ones if possible.

        :returns: None
        :rtype: None
        """
        try:
            # Get system information for requirements checking
            system_info = get_system_info()

            # Get local LLM providers from config
            local_providers = ["ollama", "lmstudio"]
            available_models = []

            for provider in local_providers:
                if provider not in self.config.get("providers", {}):
                    continue

                provider_config = self.config["providers"][provider]
                provider_endpoint = provider_config.get("endpoint", "")

                # Check if provider endpoint is available
                provider_available = self._check_provider_availability(provider, provider_endpoint)
                if not provider_available:
                    logging.warning(f"Local LLM provider {provider} is not available at {provider_endpoint}")
                    continue

                # Get models for this provider
                models_config = provider_config.get("models", {})

                for model_name, model_config in models_config.items():
                    model_id = f"{provider}/{model_name}"

                    # Check system requirements for this model
                    system_requirements = model_config.get("system_requirements", {})
                    meets_requirements, requirement_warnings = check_system_requirements(
                        system_requirements, system_info
                    )

                    if not meets_requirements:
                        logging.warning(f"System does not meet requirements for model {model_id}:")
                        for warning in requirement_warnings:
                            logging.warning(f"  - {warning}")
                        continue

                    # Check if model is already available
                    model_available = self._check_model_availability(provider, model_name, provider_endpoint)

                    if model_available:
                        logging.info(f"Local LLM model {model_id} is available")
                        available_models.append(model_id)
                    else:
                        # Try to download the model
                        logging.info(f"Local LLM model {model_id} is not available, attempting to download")
                        if self._download_local_llm_model(provider, model_name, model_config):
                            available_models.append(model_id)

            # Update available models
            if available_models:
                self.available_models["local_llm"] = available_models
                logging.info(f"Available local LLM models: {available_models}")
            else:
                logging.warning("No local LLM models available")

        except Exception as e:
            logging.error(f"Error checking local LLM: {e}")

    def _check_provider_availability(self, provider: str, endpoint: str) -> bool:
        """
        Check if a local LLM provider is available.

        :param provider: Name of the provider
        :type provider: str
        :param endpoint: Provider endpoint URL
        :type endpoint: str
        :returns: True if provider is available, False otherwise
        :rtype: bool
        """
        if not endpoint:
            return False

        try:
            if provider == "ollama":
                # Try to connect to Ollama API
                response = requests.get(f"{endpoint}/api/tags", timeout=2)
                return response.status_code == 200
            elif provider == "lmstudio":
                # Try to connect to LM Studio API
                response = requests.get(endpoint, timeout=2)
                return response.status_code == 200
            else:
                return False
        except Exception as e:
            logging.debug(f"Provider {provider} not available: {e}")
            return False

    def _check_model_availability(self, provider: str, model_name: str, endpoint: str) -> bool:
        """
        Check if a specific model is available from a provider.

        :param provider: Name of the provider
        :type provider: str
        :param model_name: Name of the model
        :type model_name: str
        :param endpoint: Provider endpoint URL
        :type endpoint: str
        :returns: True if model is available, False otherwise
        :rtype: bool
        """
        try:
            if provider == "ollama":
                # Check if model is in the list of available models
                response = requests.get(f"{endpoint}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return any(model.get("name") == model_name for model in models)
            elif provider == "lmstudio":
                # For LM Studio, we can't easily check which models are loaded
                # We'll assume it's not available and let the download process handle it
                return False
            return False
        except Exception as e:
            logging.debug(f"Error checking model availability for {provider}/{model_name}: {e}")
            return False

    def _download_local_llm_model(self, provider: str, model_name: str, model_config: dict[str, Any]) -> bool:
        """
        Download a local LLM model.

        :param provider: Name of the provider
        :type provider: str
        :param model_name: Name of the model
        :type model_name: str
        :param model_config: Configuration of the model
        :type model_config: Dict[str, Any]
        :returns: True if model was successfully downloaded, False otherwise
        :rtype: bool
        """
        try:
            model_type = model_config.get("type", "")
            if model_type != "downloadable":
                logging.warning(f"Model {provider}/{model_name} is not downloadable")
                return False

            if provider == "ollama":
                # Use Ollama's CLI to download the model
                download_command = model_config.get("download_command", f"ollama pull {model_name}")
                logging.info(f"Downloading model using command: {download_command}")

                try:
                    # Run the download command
                    process = subprocess.Popen(
                        download_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )

                    # Monitor the process and log output
                    while True:
                        output = process.stdout.readline()
                        if output == "" and process.poll() is not None:
                            break
                        if output:
                            logging.info(output.strip())

                    # Check if download was successful
                    if process.returncode == 0:
                        logging.info(f"Successfully downloaded model {provider}/{model_name}")
                        return True
                    else:
                        error = process.stderr.read()
                        logging.error(f"Failed to download model {provider}/{model_name}: {error}")
                        return False

                except Exception as e:
                    logging.error(f"Error downloading model {provider}/{model_name}: {e}")
                    return False

            elif provider == "lmstudio":
                # For LM Studio, we need to download the model file directly
                download_url = model_config.get("download_url", "")
                if not download_url:
                    logging.error(f"No download URL provided for model {provider}/{model_name}")
                    return False

                # Get file name and path
                file_name = model_config.get("file_name", f"{model_name}.bin")
                models_dir = os.path.join(os.path.expanduser("~"), ".lmstudio", "models")
                os.makedirs(models_dir, exist_ok=True)
                model_path = os.path.join(models_dir, file_name)

                # Použití generické metody pro stahování souborů
                description = f"Stahuji LLM model {provider}/{model_name}"
                download_success = download_file(
                    url=download_url,
                    destination_path=model_path,
                    description=description,
                    show_progress=True,
                    create_dirs=True,
                    overwrite=False,
                    chunk_size=1024 * 1024,  # Použijeme větší chunk size pro velké LLM modely (1MB)
                )

                if download_success:
                    logging.info(f"Úspěšně stažen LLM model {provider}/{model_name}")
                    return True
                else:
                    logging.error(f"Nepodařilo se stáhnout LLM model {provider}/{model_name}")
                    return False

            return False
        except Exception as e:
            logging.error(f"Error in download process for {provider}/{model_name}: {e}")
            return False

    def _check_online_llm(self) -> None:
        """
        Check available online LLM models.

        :returns: None
        :rtype: None
        """
        try:
            # Get online LLM providers from config
            online_providers = ["openai", "anthropic", "google", "mistral"]

            for provider in online_providers:
                if provider not in self.config.get("providers", {}):
                    continue

                provider_config = self.config["providers"][provider]

                # Check if API key is available
                api_key = provider_config.get("api_key", "")
                api_key_env = provider_config.get("api_key_env", "")

                if not api_key and api_key_env:
                    api_key = os.environ.get(api_key_env, "")

                if not api_key:
                    logging.warning(f"API key not found for {provider}")
                    continue

                # Get models for this provider
                models = provider_config.get("models", {})

                for model_name, model_config in models.items():
                    # Check if model supports image
                    supports_image = model_config.get("supports_image", False)

                    # Add model to available models
                    model_id = f"{provider}/{model_name}"
                    self.available_models["online_llm"].append(model_id)

            if self.available_models["online_llm"]:
                logging.info(f"Found online LLM models: {self.available_models['online_llm']}")

        except Exception as e:
            logging.error(f"Error checking online LLM: {e}")

    def get_model_config(self, model_id: str) -> dict[str, Any]:
        """
        Get configuration for a specific model.

        :param model_id: Model ID in the format "provider/model_name"
        :type model_id: str
        :returns: Dictionary containing model configuration
        :rtype: Dict[str, Any]
        """
        if self.config is None:
            self.load_config()

        if not self.config:
            return {}

        try:
            # Parse model ID
            provider, model_name = model_id.split("/", 1)

            # Get provider config
            provider_config = self.config.get("providers", {}).get(provider, {})

            # Get model config
            model_config = provider_config.get("models", {}).get(model_name, {})

            # Add provider info to model config
            result = {
                "provider": provider,
                "model_name": model_name,
                "endpoint": provider_config.get("endpoint", ""),
                "api_key": provider_config.get("api_key", ""),
                "api_key_env": provider_config.get("api_key_env", ""),
            }

            # Add model-specific config
            result.update(model_config)

            return result

        except Exception as e:
            logging.error(f"Error getting model config for {model_id}: {e}")
            return {}


def save_ai_config(config: dict[str, Any], config_path: str) -> bool:
    """
    Save AI configuration to JSON file.

    :param config: Dictionary containing AI configuration
    :type config: Dict[str, Any]
    :param config_path: Path to save the AI configuration file
    :type config_path: str
    :returns: True if successful, False otherwise
    :rtype: bool
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        logging.info(f"Saved AI configuration to {config_path}")
        return True

    except Exception as e:
        logging.error(f"Error saving AI configuration: {e}")
        return False


def get_system_info() -> dict[str, Any]:
    """
    Get information about the current system.

    :returns: Dictionary containing system information
    :rtype: Dict[str, Any]
    """
    try:
        # Get OS information
        os_name = platform.system().lower()
        if os_name == "darwin":
            os_name = "macos"  # Normalize macOS name

        # Get CPU information
        cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True)
        cpu_model = "Unknown"

        # Try to get CPU model name
        if os_name == "windows":
            try:
                output = subprocess.check_output("wmic cpu get name", shell=True).decode("utf-8")
                lines = output.strip().split("\n")
                if len(lines) > 1:
                    cpu_model = lines[1].strip()
            except Exception as e:
                logging.warning(f"Failed to get CPU model: {e}")
        elif os_name == "linux":
            try:
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if line.startswith("model name"):
                            cpu_model = line.split(":", 1)[1].strip()
                            break
            except Exception as e:
                logging.warning(f"Failed to get CPU model: {e}")
        elif os_name == "macos":
            try:
                output = subprocess.check_output("sysctl -n machdep.cpu.brand_string", shell=True).decode("utf-8")
                cpu_model = output.strip()
            except Exception as e:
                logging.warning(f"Failed to get CPU model: {e}")

        # Get RAM information
        ram_info = psutil.virtual_memory()
        ram_total_gb = round(ram_info.total / (1024**3), 2)  # Convert bytes to GB

        # Get GPU information (if available)
        gpu_info = get_gpu_info()

        # Combine all information
        system_info = {
            "os": {"name": os_name, "version": platform.version(), "architecture": platform.machine()},
            "cpu": {"model": cpu_model, "cores": cpu_count},
            "ram": {"total_gb": ram_total_gb, "available_gb": round(ram_info.available / (1024**3), 2)},
            "gpu": gpu_info,
        }

        logging.info(f"System information: OS={os_name}, RAM={ram_total_gb}GB, CPU={cpu_count} cores")
        if gpu_info:
            logging.info(f"GPU information: {gpu_info}")

        return system_info

    except Exception as e:
        logging.error(f"Error getting system information: {e}")
        return {"os": {"name": "unknown"}, "ram": {"total_gb": 0, "available_gb": 0}, "gpu": {"available": False}}


def get_gpu_info() -> dict[str, Any]:
    """
    Get information about available GPUs.

    :returns: Dictionary containing GPU information
    :rtype: Dict[str, Any]
    """
    gpu_info = {"available": False, "count": 0, "models": [], "total_vram_gb": 0}

    try:
        # Try to import torch to check for CUDA availability
        try:
            import torch

            if torch.cuda.is_available():
                gpu_info["available"] = True
                gpu_info["count"] = torch.cuda.device_count()
                gpu_info["models"] = [torch.cuda.get_device_name(i) for i in range(gpu_info["count"])]

                # Try to get VRAM information
                try:
                    for i in range(gpu_info["count"]):
                        # Get free and total memory in bytes, then convert to GB
                        free_mem, total_mem = torch.cuda.mem_get_info(i)
                        total_mem_gb = round(total_mem / (1024**3), 2)
                        gpu_info["total_vram_gb"] += total_mem_gb
                except Exception:
                    # If we can't get memory info, make a rough estimate based on GPU model
                    for model in gpu_info["models"]:
                        if "3090" in model or "4090" in model:
                            gpu_info["total_vram_gb"] += 24
                        elif "3080" in model or "4080" in model:
                            gpu_info["total_vram_gb"] += 16
                        elif "3070" in model or "4070" in model:
                            gpu_info["total_vram_gb"] += 8
                        elif "3060" in model or "4060" in model:
                            gpu_info["total_vram_gb"] += 6
                        else:
                            gpu_info["total_vram_gb"] += 4  # Default assumption
        except ImportError:
            logging.info("PyTorch not available, cannot check GPU information")
            pass

        # If torch failed, try platform-specific methods
        if not gpu_info["available"]:
            os_name = platform.system().lower()
            if os_name == "windows":
                try:
                    output = subprocess.check_output("wmic path win32_VideoController get name", shell=True).decode(
                        "utf-8"
                    )
                    lines = output.strip().split("\n")[1:]  # Skip header
                    gpu_models = [line.strip() for line in lines if line.strip()]

                    if gpu_models:
                        gpu_info["available"] = True
                        gpu_info["count"] = len(gpu_models)
                        gpu_info["models"] = gpu_models

                        # Rough estimate of VRAM based on GPU names
                        for model in gpu_models:
                            if "NVIDIA" in model or "GeForce" in model or "RTX" in model or "GTX" in model:
                                gpu_info["total_vram_gb"] += 4  # Conservative estimate
                except Exception as e:
                    logging.warning(f"Failed to get GPU information: {e}")

            elif os_name == "linux":
                try:
                    # Try lspci command
                    output = subprocess.check_output("lspci | grep -i 'vga\\|3d\\|2d'", shell=True).decode("utf-8")
                    if "nvidia" in output.lower() or "amd" in output.lower() or "radeon" in output.lower():
                        gpu_info["available"] = True
                        gpu_info["count"] = output.count("VGA") or output.count("3D") or 1
                        gpu_info["models"] = [
                            line.split(":")[-1].strip() for line in output.split("\n") if line.strip()
                        ]
                except Exception as e:
                    logging.warning(f"Failed to get GPU information: {e}")

    except Exception as e:
        logging.error(f"Error getting GPU information: {e}")

    return gpu_info


def check_system_requirements(requirements: dict[str, Any], system_info: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Check if the system meets the requirements for a model.

    :param requirements: Dictionary containing system requirements
    :type requirements: Dict[str, Any]
    :param system_info: Dictionary containing system information
    :type system_info: Dict[str, Any]
    :returns: Tuple of (meets_requirements, warnings)
    :rtype: Tuple[bool, List[str]]
    """
    warnings = []
    meets_requirements = True

    # Check OS compatibility
    supported_os = requirements.get("supported_os", [])
    current_os = system_info.get("os", {}).get("name", "unknown")

    if supported_os and current_os not in supported_os:
        warnings.append(
            f"Operating system '{current_os}' is not officially supported. Supported OS: {', '.join(supported_os)}"
        )
        meets_requirements = False

    # Check RAM requirements
    min_ram_gb = requirements.get("min_ram_gb", 0)
    recommended_ram_gb = requirements.get("recommended_ram_gb", min_ram_gb * 2)
    available_ram_gb = system_info.get("ram", {}).get("total_gb", 0)

    if available_ram_gb < min_ram_gb:
        warnings.append(f"Insufficient RAM: {available_ram_gb}GB available, minimum {min_ram_gb}GB required")
        meets_requirements = False
    elif available_ram_gb < recommended_ram_gb:
        warnings.append(f"Low RAM: {available_ram_gb}GB available, {recommended_ram_gb}GB recommended")

    # Check GPU requirements if the model doesn't support CPU-only operation
    cpu_only = requirements.get("cpu_only", False)
    if not cpu_only:
        min_vram_gb = requirements.get("min_vram_gb", 0)
        recommended_vram_gb = requirements.get("recommended_vram_gb", min_vram_gb * 2)
        gpu_available = system_info.get("gpu", {}).get("available", False)
        total_vram_gb = system_info.get("gpu", {}).get("total_vram_gb", 0)

        if not gpu_available:
            warnings.append("No GPU detected, but model requires GPU acceleration")
            meets_requirements = False
        elif total_vram_gb < min_vram_gb:
            warnings.append(f"Insufficient VRAM: {total_vram_gb}GB available, minimum {min_vram_gb}GB required")
            meets_requirements = False
        elif total_vram_gb < recommended_vram_gb:
            warnings.append(f"Low VRAM: {total_vram_gb}GB available, {recommended_vram_gb}GB recommended")

    return meets_requirements, warnings
