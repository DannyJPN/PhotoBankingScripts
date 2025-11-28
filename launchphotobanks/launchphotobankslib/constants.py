"""Constants for LaunchPhotobanks script."""
import os
from pathlib import Path

# Default paths
DEFAULT_BANK_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'bank_urls.csv'
)
DEFAULT_LOG_DIR = "H:/Logs"

# Bank launching configuration
DEFAULT_DELAY_BETWEEN_OPENS = 2  # seconds between opening tabs
MAX_CONCURRENT_TABS = 5  # prevent browser overload

# CSV column names
COLUMN_BANK_NAME = "BankName"
COLUMN_URL = "URL"