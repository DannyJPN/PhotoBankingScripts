"""
Constants for the markphotomediaapprovalstatus script.
"""

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
