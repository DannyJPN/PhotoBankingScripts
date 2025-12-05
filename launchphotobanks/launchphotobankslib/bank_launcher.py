"""Business logic for launching photobank login pages."""
import csv
import logging
import time
import webbrowser
from typing import Dict, List, Optional
from urllib.parse import urlparse

from launchphotobankslib.constants import COLUMN_BANK_NAME, COLUMN_URL


class BankLauncher:
    """Handles launching photobank login pages."""

    def __init__(self, csv_path: str):
        """
        Initialize with bank CSV file.

        Args:
            csv_path: Path to CSV file containing bank names and URLs
        """
        self.csv_path = csv_path
        self.banks = self._load_banks()

    def _load_banks(self) -> Dict[str, str]:
        """
        Load bank configurations from CSV file.

        Returns:
            Dictionary mapping bank name to URL

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        banks = {}
        try:
            logging.debug(f"Loading bank URLs from: {self.csv_path}")
            with open(self.csv_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Validate headers
                if COLUMN_BANK_NAME not in reader.fieldnames or COLUMN_URL not in reader.fieldnames:
                    raise ValueError(
                        f"CSV must have '{COLUMN_BANK_NAME}' and '{COLUMN_URL}' columns. "
                        f"Found: {reader.fieldnames}"
                    )

                for row_num, row in enumerate(reader, 1):
                    bank_name = row.get(COLUMN_BANK_NAME, '').strip()
                    url = row.get(COLUMN_URL, '').strip()

                    if not bank_name:
                        logging.warning(f"Row {row_num}: Missing {COLUMN_BANK_NAME}")
                        continue

                    if not url:
                        logging.warning(f"Row {row_num}: Missing {COLUMN_URL} for {bank_name}")
                        continue

                    # Validate URL format
                    if not self._is_valid_url(url):
                        logging.warning(f"Row {row_num}: Invalid URL for {bank_name}: {url}")
                        continue

                    banks[bank_name] = url
                    logging.debug(f"Loaded bank: {bank_name}")

            if not banks:
                raise ValueError(f"No valid banks loaded from {self.csv_path}")

            logging.info(f"Successfully loaded {len(banks)} banks from CSV")
            return banks

        except FileNotFoundError:
            logging.error(f"Bank CSV file not found: {self.csv_path}")
            raise
        except Exception as e:
            logging.error(f"Error loading bank CSV file {self.csv_path}: {e}")
            raise

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def get_all_bank_names(self) -> List[str]:
        """
        Get list of all available bank names.

        Returns:
            List of bank names
        """
        return list(self.banks.keys())

    def get_bank_url(self, bank_name: str) -> Optional[str]:
        """
        Get URL for specific bank.

        Args:
            bank_name: Name of the bank

        Returns:
            URL for the bank, or None if not found
        """
        return self.banks.get(bank_name)

    def launch_banks(self, bank_names: List[str], delay: int = 2) -> Dict[str, bool]:
        """
        Launch specified banks in web browser.

        Args:
            bank_names: List of bank names to launch
            delay: Delay between opening tabs in seconds

        Returns:
            Dictionary mapping bank name to success status
        """
        results = {}

        for i, bank_name in enumerate(bank_names):
            if bank_name not in self.banks:
                logging.warning(f"Unknown bank: {bank_name}")
                results[bank_name] = False
                continue

            url = self.banks[bank_name]

            try:
                logging.info(f"Opening {bank_name} ({i+1}/{len(bank_names)})")
                webbrowser.open_new_tab(url)
                logging.debug(f"Successfully opened URL: {url}")
                results[bank_name] = True

                # Delay between opens to prevent browser overload
                if i < len(bank_names) - 1 and delay > 0:
                    logging.debug(f"Waiting {delay}s before next open...")
                    time.sleep(delay)

            except Exception as e:
                logging.error(f"Failed to open {bank_name} ({url}): {e}")
                results[bank_name] = False

        # Summary
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        logging.info(f"Launch summary: {successful} successful, {failed} failed")

        return results