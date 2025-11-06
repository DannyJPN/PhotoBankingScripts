"""
Credentials manager for photobank authentication.
"""
import json
import os
import logging
import getpass
from typing import Dict, Optional


class CredentialsManager:
    """Manages photobank credentials securely."""

    def __init__(self, credentials_file: Optional[str] = None):
        """
        Initialize credentials manager.

        Args:
            credentials_file: Path to credentials JSON file (optional)
        """
        self.credentials_file = credentials_file
        self.credentials = {}

        # Load credentials from environment variables first
        self.load_from_environment()

        # Load from file only for missing photobanks
        if credentials_file and os.path.exists(credentials_file):
            self.load_missing_from_file()

    def load_from_environment(self) -> None:
        """Load credentials from environment variables."""
        logging.debug("Loading credentials from environment variables")

        # Environment variable mapping - ONE variable per credential per photobank
        photobank_env_mapping = {
            "ShutterStock": {
                "username": "SHUTTERSTOCK_USERNAME",
                "password": "SHUTTERSTOCK_PASSWORD"
            },
            "Pond5": {
                "username": "POND5_USERNAME",
                "password": "POND5_FTP_PASSWORD"
            },
            "123RF": {
                "username": "RF123_USERNAME",
                "password": "RF123_PASSWORD"
            },
            "DepositPhotos": {
                "username": "DEPOSITPHOTOS_EMAIL",
                "password": "DEPOSITPHOTOS_PASSWORD"
            },
            "Alamy": {
                "username": "ALAMY_EMAIL",
                "password": "ALAMY_PASSWORD"
            },
            "Dreamstime": {
                "username": "DREAMSTIME_USERNAME",
                "password": "DREAMSTIME_PASSWORD"
            },
            "AdobeStock": {
                "username": "ADOBESTOCK_SFTP_ID",
                "password": "ADOBESTOCK_SFTP_PASSWORD"
            },
            "CanStockPhoto": {
                "username": "CANSTOCKPHOTO_USERNAME",
                "password": "CANSTOCKPHOTO_PASSWORD"
            }
        }

        loaded_count = 0
        for photobank, env_vars in photobank_env_mapping.items():
            creds = {}

            # Load each credential field from single environment variable
            for field, env_name in env_vars.items():
                value = os.getenv(env_name)
                if value:
                    creds[field] = value
                    logging.debug(f"Loaded {field} for {photobank} from {env_name}")

            # Only store if we have username and password
            if "username" in creds and "password" in creds:
                # Fix Adobe Stock password if it has double backslash at end
                if photobank == "AdobeStock" and creds["password"].endswith("\\\\"):
                    creds["password"] = creds["password"][:-1]  # Remove last backslash
                    logging.debug(f"Fixed Adobe Stock password - removed extra backslash")

                self.credentials[photobank] = creds
                loaded_count += 1
                logging.info(f"Loaded credentials for {photobank} from environment")

        if loaded_count > 0:
            logging.info(f"Loaded credentials for {loaded_count} photobank(s) from environment variables")

    def load_missing_from_file(self) -> bool:
        """Load credentials from file only for photobanks not loaded from environment."""
        if not self.credentials_file or not os.path.exists(self.credentials_file):
            logging.warning("Credentials file not found")
            return False

        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                file_credentials = json.load(f)

            loaded_count = 0
            for photobank, creds in file_credentials.items():
                # Skip if already loaded from environment
                if photobank not in self.credentials:
                    self.credentials[photobank] = creds
                    loaded_count += 1
                    logging.info(f"Loaded credentials for {photobank} from file (fallback)")
                else:
                    logging.debug(f"Skipping {photobank} from file - already loaded from environment")

            if loaded_count > 0:
                logging.info(f"Loaded credentials for {loaded_count} additional photobank(s) from file")
            return True

        except Exception as e:
            logging.error(f"Failed to load credentials from file: {e}")
            return False

    def load_credentials(self) -> bool:
        """Load credentials from file."""
        if not self.credentials_file or not os.path.exists(self.credentials_file):
            logging.warning("Credentials file not found")
            return False

        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                self.credentials = json.load(f)
            logging.info(f"Loaded credentials for {len(self.credentials)} photobanks")
            return True
        except Exception as e:
            logging.error(f"Failed to load credentials: {e}")
            return False

    def save_credentials(self) -> bool:
        """Save credentials to file."""
        if not self.credentials_file:
            logging.error("No credentials file specified")
            return False

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)

            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(self.credentials, f, indent=2)
            logging.info(f"Saved credentials to {self.credentials_file}")
            return True
        except Exception as e:
            logging.error(f"Failed to save credentials: {e}")
            return False

    def get_credentials(self, photobank: str) -> Optional[Dict[str, str]]:
        """Get credentials for a specific photobank."""
        return self.credentials.get(photobank)

    def set_credentials(self, photobank: str, username: str, password: str, **kwargs) -> None:
        """
        Set credentials for a photobank.

        Args:
            photobank: Name of the photobank
            username: Username or email
            password: Password
            **kwargs: Additional parameters (e.g., content_type for 123RF)
        """
        self.credentials[photobank] = {
            "username": username,
            "password": password,
            **kwargs
        }
        logging.debug(f"Set credentials for {photobank}")

    def remove_credentials(self, photobank: str) -> bool:
        """Remove credentials for a photobank."""
        if photobank in self.credentials:
            del self.credentials[photobank]
            logging.info(f"Removed credentials for {photobank}")
            return True
        return False

    def list_photobanks(self) -> list:
        """List photobanks with stored credentials."""
        return list(self.credentials.keys())

    def prompt_for_credentials(self, photobank: str, save: bool = True) -> bool:
        """
        Interactively prompt for credentials.

        Args:
            photobank: Name of the photobank
            save: Whether to save credentials to file

        Returns:
            True if credentials were entered, False otherwise
        """
        print(f"\nEnter credentials for {photobank}:")

        username = input("Username/Email: ").strip()
        if not username:
            print("Username is required")
            return False

        password = getpass.getpass("Password: ").strip()
        if not password:
            print("Password is required")
            return False

        # Special handling for photobanks with additional requirements
        kwargs = {}

        if photobank == "123RF":
            print("\nNote: 123RF content type is automatically determined based on file type.")
            print("The system will use photos/video/audio servers as appropriate.")

        elif photobank == "Pond5":
            print("\nNote: Pond5 requires a separate FTP password.")
            print("Please generate an FTP password in your Pond5 account settings.")

        elif photobank == "AdobeStock":
            print("\nNote: Adobe Stock requires SFTP credentials.")
            print("Please generate SFTP credentials in your Adobe Stock contributor portal.")
            print("Use the numeric user ID (not email) as username.")

        self.set_credentials(photobank, username, password, **kwargs)

        if save and self.credentials_file:
            return self.save_credentials()

        return True

    def validate_credentials_format(self, photobank: str) -> bool:
        """Validate that credentials have the required format for the photobank."""
        creds = self.get_credentials(photobank)
        if not creds:
            return False

        # Check required fields
        if not creds.get("username") or not creds.get("password"):
            logging.error(f"Missing username or password for {photobank}")
            return False

        # Photobank-specific validation
        if photobank == "AdobeStock":
            # Adobe Stock should use numeric user ID
            username = creds["username"]
            if not username.isdigit():
                logging.warning(f"Adobe Stock username should be numeric ID, got: {username}")

        elif photobank == "123RF":
            # 123RF content type will be determined dynamically based on file type
            pass

        return True

    def create_credentials_template(self, file_path: str) -> bool:
        """Create a template credentials file."""
        template = {
            "ShutterStock": {
                "username": "your_username_or_email",
                "password": "your_password"
            },
            "Pond5": {
                "username": "your_pond5_username",
                "password": "your_ftp_password_from_account_settings"
            },
            "123RF": {
                "username": "your_123rf_username",
                "password": "your_password"
            },
            "DepositPhotos": {
                "username": "your_email",
                "password": "your_password"
            },
            "Alamy": {
                "username": "your_email",
                "password": "your_password"
            },
            "Dreamstime": {
                "username": "your_username_or_userid",
                "password": "your_password"
            },
            "AdobeStock": {
                "username": "your_numeric_sftp_id",
                "password": "your_generated_sftp_password"
            }
        }

        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2)
            logging.info(f"Created credentials template at {file_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to create credentials template: {e}")
            return False

    def get_all_credentials(self) -> Dict[str, Dict[str, str]]:
        """Get all stored credentials."""
        return self.credentials.copy()

    def has_credentials(self, photobank: str) -> bool:
        """Check if credentials exist for a photobank."""
        return photobank in self.credentials

    def clear_all_credentials(self) -> None:
        """Clear all stored credentials."""
        self.credentials.clear()
        logging.info("Cleared all credentials")