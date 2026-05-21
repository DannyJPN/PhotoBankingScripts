"""
Constants for the markphotomediaapprovalstatus script.
"""

import os

# List of photobanks to check
BANKS = [
    # Active banks
    "ShutterStock",
    "AdobeStock",
    "Dreamstime",
    "DepositPhotos",
    "123RF",
    "Pond5",
    "GettyImages",
    "Alamy",
    # Deprecated banks (kept for historical data)
    "BigStockPhoto",
    "CanStockPhoto",
    # New banks
    "Pixta",
    "Freepik",
    "Vecteezy",
    "StoryBlocks",
    "Envato",
    "500px",
    "MostPhotos"
]

# Default paths
DEFAULT_PHOTO_CSV_PATH = "L:/Můj disk/XLS/Fotobanky/PhotoMedia.csv"
DEFAULT_LOG_DIR = "H:/Logs"

# Column identifiers
STATUS_COLUMN_KEYWORD = "status"
COL_FILE = "Soubor"
COL_PATH = "Cesta"
COL_ORIGINAL = "Originál"

# Original values
ORIGINAL_YES = "ano"

# Edit type suffixes
EDIT_SHARPEN = "_sharpen"

# Alternative edit tags for processed versions
ALTERNATIVE_EDIT_TAGS = {
    "_bw": "Black and white",
    "_negative": "Color negative",
    "_sharpen": "Sharpened",
    "_misty": "Misty/foggy effect",
    "_blurred": "Gaussian blur"
}

# Status values
STATUS_CHECKED = "kontrolováno"
STATUS_APPROVED = "schváleno"
STATUS_REJECTED = "zamítnuto"
STATUS_MAYBE = "schváleno?"
STATUS_BACKUP = "záložní"  # For _sharpen alternatives - ready but not for immediate upload
STATUS_PREPARED = "připraveno"  # Ready for upload
STATUS_UNUSED = "nepoužito"  # Alternative not needed (original was approved)

# User input options
INPUT_APPROVE = "a"
INPUT_REJECT = "n"
INPUT_MAYBE = "m"

# File numbering system constants
MIN_NUMBER_WIDTH = 4  # Minimum width for backward compatibility with existing files
MAX_NUMBER_WIDTH = 6  # Maximum width for new capacity
DEFAULT_NUMBER_WIDTH = 6  # Default width for new file generation
MAX_NUMBER = 999999  # Maximum number with 6 digits

# Detection thresholds
PHASH_THRESHOLD = 2          # max Hamming distance for FOUND verdict (main pipeline)
COMBINED_HASH_THRESHOLD = 19  # max phash+dhash combined distance for FOUND verdict (validator stage 2)

# Default paths for detection pipeline
DEFAULT_REPORT_DIR = "H:/Logs/auto_detection"
DEFAULT_HASH_CACHE_PATH = "L:/Můj disk/XLS/Fotobanky/.hash_cache.db"
DEFAULT_PREVIEW_CACHE_DIR = "L:/Můj disk/XLS/Fotobanky/.preview_cache"

# Pond5 portfolio CSV cache — local to markphotomediaapprovalstatusauto/, not on L:
# Kumulativní seznam asset_id + cdn_url; přetrvává mezi běhy a nikdy neztrácí záznamy.
DEFAULT_POND5_PORTFOLIO_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "pond5_portfolio_cache.csv"
)

# Contributor identity (set per-user in config)
DEFAULT_CONTRIBUTOR_NAME = ""
