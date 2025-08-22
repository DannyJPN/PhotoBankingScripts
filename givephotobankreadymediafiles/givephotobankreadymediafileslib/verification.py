"""
Verification module for checking the availability of required resources.

This module provides functions to verify:
1. CSV files existence and validity
2. Neural network models availability
3. Local LLM availability
4. Online LLM API access
5. Existence of unprocessed media files
"""

import logging
import os

from givephotobankreadymediafileslib.constants import COL_FILE, COL_PATH, COL_STATUS_SUFFIX, STATUS_UNPROCESSED
from givephotobankreadymediafileslib.data_loader import load_categories_csv, load_media_csv
from givephotobankreadymediafileslib.metadata.local_llm_generator import LocalLLMMetadataGenerator
from givephotobankreadymediafileslib.metadata.neural_generator import NeuralMetadataGenerator
from givephotobankreadymediafileslib.metadata.online_llm_generator import OnlineLLMMetadataGenerator


class SystemVerifier:
    """Class for verifying system requirements and resources."""

    def __init__(self):
        """Initialize the system verifier."""
        # No need to initialize csv_loader anymore
        self.verification_results = {
            "csv_files": False,
            "neural_networks": False,
            "local_llm": False,
            "online_llm": False,
            "unprocessed_files": False,
        }
        self.error_messages = []

    def verify_csv_files(self, media_csv_path: str, categories_csv_path: str) -> bool:
        """
        Verify that CSV files exist and are valid.

        Args:
            media_csv_path: Path to the media CSV file
            categories_csv_path: Path to the categories CSV file

        Returns:
            True if CSV files are valid, False otherwise
        """
        logging.info(f"Verifying CSV files: media={media_csv_path}, categories={categories_csv_path}")
        try:
            # Check if files exist
            if not os.path.exists(media_csv_path):
                error_msg = f"Media CSV file not found: {media_csv_path}"
                logging.error(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["csv_files"] = False
                return False
            else:
                logging.debug(f"Media CSV file exists: {media_csv_path}")

            if not os.path.exists(categories_csv_path):
                error_msg = f"Categories CSV file not found: {categories_csv_path}"
                logging.error(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["csv_files"] = False
                return False
            else:
                logging.debug(f"Categories CSV file exists: {categories_csv_path}")

            # Load media CSV
            logging.debug("Loading media CSV file")
            media_df = load_media_csv(media_csv_path)
            if media_df.empty:
                error_msg = f"Media CSV file is empty: {media_csv_path}"
                logging.error(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["csv_files"] = False
                return False
            else:
                logging.debug(f"Media CSV loaded with {len(media_df)} records")

            # Check required columns in media CSV
            required_columns = [COL_FILE, COL_PATH]
            missing_columns = [col for col in required_columns if col not in media_df.columns]
            if missing_columns:
                error_msg = f"Missing required columns in media CSV: {missing_columns}"
                logging.error(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["csv_files"] = False
                return False
            else:
                logging.debug(f"All required columns present in media CSV: {required_columns}")

            # Load categories CSV
            logging.debug("Loading categories CSV file")
            photobank_categories = load_categories_csv(categories_csv_path)
            if not photobank_categories:
                error_msg = f"No categories found in categories CSV: {categories_csv_path}"
                logging.error(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["csv_files"] = False
                return False
            else:
                logging.debug(f"Categories CSV loaded with {len(photobank_categories)} categories")

            # All checks passed
            logging.info("CSV files verification successful")
            self.verification_results["csv_files"] = True
            return True

        except Exception as e:
            error_msg = f"Error verifying CSV files: {e}"
            logging.error(error_msg)
            self.error_messages.append(error_msg)
            self.verification_results["csv_files"] = False
            return False

    def verify_neural_networks(self, models_dir: str) -> bool:
        """
        Verify that neural network models are available.

        Args:
            models_dir: Directory containing neural network models

        Returns:
            True if neural network models are available, False otherwise
        """
        logging.info(f"Verifying neural network models in directory: {models_dir}")
        try:
            # Check if models directory exists
            if not os.path.exists(models_dir):
                error_msg = f"Neural network models directory not found: {models_dir}"
                logging.error(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["neural_networks"] = False
                return False

            # Check if there are any model files
            model_files = [f for f in os.listdir(models_dir) if f.endswith(".pt")]
            logging.debug(f"Found {len(model_files)} model files in {models_dir}")
            if not model_files:
                error_msg = f"No neural network model files found in: {models_dir}"
                logging.error(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["neural_networks"] = False
                return False

            # Try to initialize neural network generator
            try:
                logging.debug("Initializing neural network generator")
                generator = NeuralMetadataGenerator(models_dir=models_dir)
                logging.debug(f"Loaded models: {list(generator.models.keys())}")
                if not generator.models:
                    error_msg = f"No valid neural network models found in: {models_dir}"
                    logging.error(error_msg)
                    self.error_messages.append(error_msg)
                    self.verification_results["neural_networks"] = False
                    return False
            except Exception as e:
                error_msg = f"Error initializing neural network generator: {e}"
                logging.error(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["neural_networks"] = False
                return False

            # All checks passed
            logging.info(f"Successfully verified neural network models: {list(generator.models.keys())}")
            self.verification_results["neural_networks"] = True
            return True

        except Exception as e:
            error_msg = f"Error verifying neural networks: {e}"
            logging.error(error_msg)
            self.error_messages.append(error_msg)
            self.verification_results["neural_networks"] = False
            return False

    def verify_local_llm(self, model_name: str = "llama3", endpoint: str = "http://localhost:11434") -> bool:
        """
        Verify that local LLM is available.

        Args:
            model_name: Name of the local LLM model
            endpoint: API endpoint for the local LLM service

        Returns:
            True if local LLM is available, False otherwise
        """
        logging.info(f"Verifying local LLM model: {model_name} at endpoint: {endpoint}")
        try:
            # Try to initialize local LLM generator
            try:
                logging.debug("Initializing local LLM generator")
                generator = LocalLLMMetadataGenerator(model_name=model_name, endpoint=endpoint)
                logging.debug(f"Local LLM generator initialized with model: {model_name}")

                # Try a simple test query
                logging.debug("Testing local LLM with a simple query")
                response = generator.llm_client.generate_text("Test")
                logging.debug(
                    f"Local LLM response received: {response[:50]}..." if response and len(response) > 50 else response
                )

                if not response:
                    error_msg = f"Local LLM returned empty response: {model_name}"
                    logging.error(error_msg)
                    self.error_messages.append(error_msg)
                    self.verification_results["local_llm"] = False
                    return False
            except Exception as e:
                error_msg = f"Error initializing local LLM generator: {e}"
                logging.error(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["local_llm"] = False
                return False

            # All checks passed
            logging.info(f"Successfully verified local LLM model: {model_name}")
            self.verification_results["local_llm"] = True
            return True

        except Exception as e:
            error_msg = f"Error verifying local LLM: {e}"
            logging.error(error_msg)
            self.error_messages.append(error_msg)
            self.verification_results["local_llm"] = False
            return False

    def verify_online_llm(
        self, provider: str = "openai", model_name: str = "gpt-3.5-turbo", api_key: str | None = None
    ) -> bool:
        """
        Verify that online LLM API access is available.

        Args:
            provider: Name of the API provider
            model_name: Name of the model to use
            api_key: API key for the service

        Returns:
            True if online LLM API access is available, False otherwise
        """
        logging.info(f"Verifying online LLM: provider={provider}, model={model_name}")
        try:
            # Try to initialize online LLM generator
            try:
                logging.debug("Initializing online LLM generator")
                generator = OnlineLLMMetadataGenerator(provider=provider, model_name=model_name, api_key=api_key)
                logging.debug(f"Online LLM generator initialized with provider: {provider}, model: {model_name}")

                # Check if API key is available
                if not generator.llm_client.api_key:
                    error_msg = f"API key not found for {provider}"
                    logging.error(error_msg)
                    self.error_messages.append(error_msg)
                    self.verification_results["online_llm"] = False
                    return False
                else:
                    logging.debug(f"API key found for provider: {provider}")

                # Try a simple test query (optional, may incur costs)
                # Uncomment if you want to actually test the API connection
                # logging.debug("Testing online LLM with a simple query")
                # response = generator.llm_client.generate_text("Test")
                # logging.debug(f"Online LLM response received: {response[:50]}..." if response and len(response) > 50 else response)
                # if not response:
                #     error_msg = f"Online LLM returned empty response: {provider} {model_name}"
                #     logging.error(error_msg)
                #     self.error_messages.append(error_msg)
                #     self.verification_results["online_llm"] = False
                #     return False
            except Exception as e:
                error_msg = f"Error initializing online LLM generator: {e}"
                logging.error(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["online_llm"] = False
                return False

            # All checks passed
            logging.info(f"Successfully verified online LLM: provider={provider}, model={model_name}")
            self.verification_results["online_llm"] = True
            return True

        except Exception as e:
            error_msg = f"Error verifying online LLM: {e}"
            logging.error(error_msg)
            self.error_messages.append(error_msg)
            self.verification_results["online_llm"] = False
            return False

    def verify_unprocessed_files(self, media_csv_path: str) -> bool:
        """
        Verify that there are unprocessed media files.

        Args:
            media_csv_path: Path to the media CSV file

        Returns:
            True if there are unprocessed media files, False otherwise
        """
        logging.info(f"Verifying unprocessed media files in: {media_csv_path}")
        try:
            # Load media CSV
            logging.debug("Loading media CSV file to check for unprocessed files")
            media_df = load_media_csv(media_csv_path)
            if media_df.empty:
                error_msg = f"Media CSV file is empty: {media_csv_path}"
                logging.error(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["unprocessed_files"] = False
                return False

            # Check for unprocessed files
            unprocessed_files = []

            # Check if any status column exists
            status_columns = [col for col in media_df.columns if col.lower().endswith(COL_STATUS_SUFFIX)]
            logging.debug(f"Found status columns: {status_columns}")

            if status_columns:
                logging.debug("Checking for unprocessed files using status columns")
                # Find records with unprocessed status in any status column
                for _, row in media_df.iterrows():
                    file_path = row.get(COL_PATH, "")
                    if not file_path or not os.path.exists(file_path):
                        continue

                    # Check if any status column has unprocessed status
                    for status_col in status_columns:
                        if row.get(status_col) == STATUS_UNPROCESSED:
                            unprocessed_files.append(file_path)
                            logging.debug(f"Found unprocessed file: {file_path}")
                            break
            else:
                logging.debug("No status columns found, considering all files as unprocessed")
                # If no status columns, consider all files as unprocessed
                for _, row in media_df.iterrows():
                    file_path = row.get(COL_PATH, "")
                    if file_path and os.path.exists(file_path):
                        unprocessed_files.append(file_path)
                        logging.debug(f"Found file to process: {file_path}")

            if not unprocessed_files:
                error_msg = "No unprocessed media files found"
                logging.warning(error_msg)
                self.error_messages.append(error_msg)
                self.verification_results["unprocessed_files"] = False
                return False

            # All checks passed
            logging.info(f"Found {len(unprocessed_files)} unprocessed media files")
            self.verification_results["unprocessed_files"] = True
            return True

        except Exception as e:
            error_msg = f"Error verifying unprocessed files: {e}"
            logging.error(error_msg)
            self.error_messages.append(error_msg)
            self.verification_results["unprocessed_files"] = False
            return False

    def verify_all(
        self,
        media_csv_path: str,
        categories_csv_path: str,
        models_dir: str,
        verify_local_llm: bool = True,
        verify_online_llm: bool = True,
    ) -> bool:
        """
        Verify all requirements.

        Args:
            media_csv_path: Path to the media CSV file
            categories_csv_path: Path to the categories CSV file
            models_dir: Directory containing neural network models
            verify_local_llm: Whether to verify local LLM
            verify_online_llm: Whether to verify online LLM

        Returns:
            True if all requirements are met, False otherwise
        """
        logging.info("Starting system verification")
        logging.debug(
            f"Verification parameters: media_csv={media_csv_path}, categories_csv={categories_csv_path}, models_dir={models_dir}"
        )
        logging.debug(
            f"Verification options: verify_local_llm={verify_local_llm}, verify_online_llm={verify_online_llm}"
        )

        # Clear previous results
        self.verification_results = {
            "csv_files": False,
            "neural_networks": False,
            "local_llm": False,
            "online_llm": False,
            "unprocessed_files": False,
        }
        self.error_messages = []

        # Verify CSV files
        logging.info("Verifying CSV files")
        csv_files_ok = self.verify_csv_files(media_csv_path, categories_csv_path)
        logging.debug(f"CSV files verification result: {csv_files_ok}")

        # Verify neural networks
        logging.info("Verifying neural networks")
        neural_networks_ok = self.verify_neural_networks(models_dir)
        logging.debug(f"Neural networks verification result: {neural_networks_ok}")

        # Verify local LLM
        local_llm_ok = True
        if verify_local_llm:
            logging.info("Verifying local LLM")
            local_llm_ok = self.verify_local_llm()
            logging.debug(f"Local LLM verification result: {local_llm_ok}")
        else:
            logging.info("Skipping local LLM verification")
            self.verification_results["local_llm"] = True

        # Verify online LLM
        online_llm_ok = True
        if verify_online_llm:
            logging.info("Verifying online LLM")
            online_llm_ok = self.verify_online_llm()
            logging.debug(f"Online LLM verification result: {online_llm_ok}")
        else:
            logging.info("Skipping online LLM verification")
            self.verification_results["online_llm"] = True

        # Verify unprocessed files
        logging.info("Verifying unprocessed files")
        unprocessed_files_ok = self.verify_unprocessed_files(media_csv_path)
        logging.debug(f"Unprocessed files verification result: {unprocessed_files_ok}")

        # All checks must pass
        all_ok = csv_files_ok and neural_networks_ok and local_llm_ok and online_llm_ok and unprocessed_files_ok

        if all_ok:
            logging.info("All system verification checks passed successfully")
        else:
            logging.warning("Some system verification checks failed")
            logging.warning(self.get_error_message())

        return all_ok

    def get_error_message(self) -> str:
        """
        Get a formatted error message with all verification errors.

        Returns:
            Formatted error message
        """
        if not self.error_messages:
            return "No errors"

        return "Verification errors:\n" + "\n".join(f"- {msg}" for msg in self.error_messages)
