"""
Constants for the MarkMediaAsChecked script.
"""

DEFAULT_PHOTO_CSV_FILE = "L:\\Můj disk\\XLS\\Fotobanky\\PhotoMedia.csv"
STATUS_COLUMN_KEYWORD = "status"

# Status values
STATUS_READY = "připraveno"
STATUS_CHECKED = "kontrolováno"

# Default log directory
DEFAULT_LOG_DIR = "H:/Logs"
DEFAULT_REPORT_DIR = "H:/Logs/MarkMediaAsChecked"

# Column names
COL_FILE = "Soubor"
COL_PATH = "Cesta"

# Alternative edit tags for processed versions
ALTERNATIVE_EDIT_TAGS = {
    "_bw": "Black and white",
    "_negative": "Color negative",
    "_sharpen": "Sharpened",
    "_misty": "Misty/foggy effect",
    "_blurred": "Gaussian blur"
}

# File numbering system constants
MIN_NUMBER_WIDTH = 4  # Minimum width for backward compatibility with existing files
MAX_NUMBER_WIDTH = 6  # Maximum width for new capacity
DEFAULT_NUMBER_WIDTH = 6  # Default width for new file generation
MAX_NUMBER = 999999  # Maximum number with 6 digits
