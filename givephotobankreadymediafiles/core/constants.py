"""
Constants for the photobank metadata generation system.
"""
import os

# Status constants
STATUS_UNPROCESSED = "nezpracováno"
STATUS_PROCESSED = "zpracováno"
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
COL_STATUS_PREFIX = "status_"

# Original flag values
ORIGINAL_YES = "ano"
ORIGINAL_NO = "ne"

# Default paths for models
DEFAULT_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "models")
DEFAULT_TRAINING_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "training")

# LLM settings
DEFAULT_LLM_TIMEOUT = 30  # seconds
DEFAULT_LLM_MAX_TOKENS = 1000

# Prompts for LLM
TITLE_PROMPT = """Generate a concise, descriptive title for this image that would be suitable for a stock photo website. 
The title should be clear, specific, and under 80 characters.
Describe the main subject and context without using unnecessary adjectives.
Do not use phrases like "stock photo" or "image of" in the title."""

DESCRIPTION_PROMPT = """Write a detailed description for this image for a stock photo website.
The description should be factual, specific, and under 200 characters.
Include the main subject, setting, action, and mood if relevant.
Do not use phrases like "stock photo" or "image shows" in the description."""

KEYWORDS_PROMPT = """Generate a list of relevant keywords for this image for a stock photo website.
Include specific objects, concepts, actions, emotions, and settings visible in the image.
Provide 10-20 keywords, separated by commas.
Include both specific and general terms to maximize searchability.
Do not include redundant or overly similar keywords."""

CATEGORIES_PROMPT = """Based on the image content, select the most appropriate category from the following list:
{categories}
Return only the exact category name from the list that best matches the image content."""
