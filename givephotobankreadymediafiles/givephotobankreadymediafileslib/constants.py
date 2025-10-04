"""
Constants for the photobank metadata generation system.
"""
import os

# Status constants
STATUS_UNPROCESSED = "nezpracováno"
STATUS_PREPARED = "připraveno"
STATUS_REJECTED = "zamítnuto"
STATUS_ERROR = "chyba"

# File types
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.dng', '.nef', '.raw', '.cr2', '.arw']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.wmv', '.mkv']
VECTOR_EXTENSIONS = ['.svg', '.eps', '.ai']

# Metadata constraints
MAX_TITLE_LENGTH = 80
MAX_DESCRIPTION_LENGTH = 200
MAX_KEYWORDS_COUNT = 50

# AI generation settings
AI_MAX_RETRY_ATTEMPTS = 10

# CSV column names
COL_FILE = "Soubor"
COL_TITLE = "Název"
COL_DESCRIPTION = "Popis"
COL_PREP_DATE = "Datum přípravy"
COL_WIDTH = "Šířka"
COL_HEIGHT = "Výška"
COL_RESOLUTION = "Rozlišení"
COL_KEYWORDS = "Klíčová slova"
COL_CATEGORIES = "Kategorie"
COL_CREATE_DATE = "Datum vytvoření"
COL_ORIGINAL = "Originál"
COL_PATH = "Cesta"
# Dynamic column name patterns for photobanks
COL_STATUS_SUFFIX = " status"
COL_CATEGORY_SUFFIX = " kategorie"

def get_status_column(photobank: str) -> str:
    """Get status column name for given photobank."""
    return f"{photobank}{COL_STATUS_SUFFIX}"

def get_category_column(photobank: str) -> str:
    """Get category column name for given photobank."""
    return f"{photobank}{COL_CATEGORY_SUFFIX}"

# Original flag values
ORIGINAL_YES = "ano"
ORIGINAL_NO = "ne"



# Alternative edit tags for processed versions
ALTERNATIVE_EDIT_TAGS = {
    "_bw": "Black and white",
    "_negative": "Color negative",
    "_sharpen": "Sharpened",
    "_misty": "Misty/foggy effect",
    "_blurred": "Gaussian blur"
}

# Alternative output formats (beyond original JPG)
ALTERNATIVE_FORMATS = ['.png', '.tif']

# User-friendly effect names mapping to technical tags
EFFECT_NAME_MAPPING = {
    "blackwhite": "_bw",
    "bw": "_bw",
    "grayscale": "_bw",
    "negative": "_negative",
    "invert": "_negative",
    "sharpen": "_sharpen",
    "sharp": "_sharpen",
    "misty": "_misty",
    "foggy": "_misty",
    "fog": "_misty",
    "blur": "_blurred",
    "blurred": "_blurred",
    "soft": "_blurred"
}

# User-friendly format names mapping to technical extensions
FORMAT_NAME_MAPPING = {
    "png": ".png",
    "tif": ".tif",
    "tiff": ".tif"
}

# Default alternatives configuration (user-friendly names)
DEFAULT_ALTERNATIVE_EFFECTS = "blackwhite,negative,sharpen,misty,blur"
DEFAULT_ALTERNATIVE_FORMATS = "png,tif"

# File extensions allowed in CSV database (JPG, video, vector formats - no PNG/TIF)
CSV_ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.mp4', '.avi', '.mov', '.wmv', '.svg', '.eps', '.ai']

# Default paths for files and directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Default paths from original scripts
DEFAULT_MEDIA_CSV_PATH = r"L:\Můj disk\XLS\Fotobanky\PhotoMedia.csv"
DEFAULT_LIMITS_CSV_PATH = r"L:\Můj disk\XLS\Fotobanky\PhotoLimits.csv"
DEFAULT_CATEGORIES_CSV_PATH = r"L:\Můj disk\XLS\Fotobanky\PhotoCategories.csv"

# Default log directory
DEFAULT_LOG_DIR = r"H:\Logs"

# Processing settings
DEFAULT_PROCESSED_MEDIA_MAX_COUNT = 20
DEFAULT_INTERVAL = 60