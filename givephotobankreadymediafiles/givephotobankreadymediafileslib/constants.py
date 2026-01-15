"""
Constants for the photobank metadata generation system.
"""
import os

# Status constants
STATUS_UNPROCESSED = "nezpracováno"
STATUS_PREPARED = "připraveno"
STATUS_BACKUP = "záložní"  # For _sharpen alternatives - ready but not for immediate upload
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
COL_EDITORIAL = "Editorial"
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

# Status values
STATUS_REJECTED = "zamítnuto"

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
DEFAULT_ALTERNATIVE_EFFECTS = "blackwhite,negative,sharpen"
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

# Batch mode defaults
DEFAULT_BATCH_MODE = False
DEFAULT_BATCH_SIZE = 20  # Total photos to collect per run; split into 20-photo vision batches
DEFAULT_BATCH_WAIT_TIMEOUT = 3600  # 0 = unlimited wait for batch completion
DEFAULT_BATCH_POLL_INTERVAL = 600  # Poll OpenAI API every 10 minutes (batches typically take 10-30 min)
DEFAULT_MAX_POLL_ITERATIONS = 1000  # Maximum polling cycles before timeout (~5 hours at 18s interval)
DEFAULT_BATCH_DESCRIPTION_MIN_LENGTH = 50  # Minimum user description length for quality
DEFAULT_BATCH_CLEANUP_DAYS = 365  # Delete completed batches older than 1 year
DEFAULT_ALTERNATIVE_BATCH_SIZE = 2000
DEFAULT_DAILY_BATCH_LIMIT = 500
BATCH_IMAGE_MAX_BASE64_BYTES = 5 * 1024 * 1024
DEFAULT_BATCH_VISION_SIZE = 20

# Batch status constants
BATCH_STATUS_COLLECTING = "collecting"
BATCH_STATUS_READY = "ready"
BATCH_STATUS_SENT = "sent"
BATCH_STATUS_COMPLETED = "completed"
BATCH_STATUS_ERROR = "error"

# Batch type constants
BATCH_TYPE_ORIGINALS = "originals"
BATCH_TYPE_ALTERNATIVES_BW = "alternatives_bw"
BATCH_TYPE_ALTERNATIVES_NEGATIVE = "alternatives_negative"
BATCH_TYPE_ALTERNATIVES_SHARPEN = "alternatives_sharpen"
BATCH_TYPE_ALTERNATIVES_MISTY = "alternatives_misty"
BATCH_TYPE_ALTERNATIVES_BLURRED = "alternatives_blurred"

# Batch validation limits
BATCH_SIZE_MIN = 1
BATCH_SIZE_MAX = 100
OPENAI_BATCH_SIZE_LIMIT_MB = 100  # OpenAI JSONL file size limit
OPENAI_DAILY_BATCH_LIMIT = 500  # OpenAI batches per day limit (matches DEFAULT_DAILY_BATCH_LIMIT)

BATCH_STATE_DIR = os.path.join(BASE_DIR, "batch_state")
BATCH_REGISTRY_FILE = os.path.join(BATCH_STATE_DIR, "batch_registry.json")
BATCH_LOCK_FILE = os.path.join(BATCH_STATE_DIR, "batch.lock")
BATCH_COST_LOG = os.path.join(BATCH_STATE_DIR, "cost_log.json")

# Ollama AI settings
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_TIMEOUT = 300

DEFAULT_OLLAMA_MODELS = [
    "llava:7b",
    "llava:13b",
    "llava:34b",
    "llava:7b-v1.6",
    "llava:13b-v1.6",
    "llava:34b-v1.6",
    "bakllava:7b",
    "llama3.2-vision:11b",
    "llama3.2-vision:90b",
    "cogvlm:17b"
]

DEFAULT_OLLAMA_VISION_MODEL = "llava:7b-v1.6"

# Photobank category counts (verified 2025 research)
PHOTOBANK_CATEGORY_COUNTS = {
    'shutterstock': 2,   # Up to 2 categories
    'adobestock': 1,     # 1 category
    'dreamstime': 3,     # Up to 3 categories
    'alamy': 2,          # Primary + optional Secondary
    'depositphotos': 0,
    'bigstockphoto': 0,
    '123rf': 0,
    'canstockphoto': 0,
    'pond5': 0,
    'gettyimages': 0,
    # New banks
    'pixta': 0,
    'freepik': 0,
    'vecteezy': 0,
    'storyblocks': 0,
    'envato': 0,
    '500px': 0,
    'mostphotos': 0
}
