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
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".dng", ".nef", ".raw", ".cr2", ".arw"]
VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".wmv", ".mkv"]
VECTOR_EXTENSIONS = [".svg", ".eps", ".ai"]

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
COL_STATUS_SUFFIX = " status"
COL_CATEGORY_SUFFIX = " kategorie"

# Original flag values
ORIGINAL_YES = "ano"
ORIGINAL_NO = "ne"

# Default paths for files and directories
# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Default paths from original scripts
DEFAULT_MEDIA_CSV_PATH = r"L:\Můj disk\XLS\Fotobanky/PhotoMedia.csv"
DEFAULT_LIMITS_CSV_PATH = r"L:\Můj disk\XLS\Fotobanky/PhotoLimits.csv"
DEFAULT_CATEGORIES_CSV_PATH = r"L:\Můj disk\XLS\Fotobanky/PhotoCategories.csv"

# COCO categories file
COCO_CATEGORIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "coco_categories.txt")
COCO_CATEGORIES_URL = (
    "https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/datasets/coco.yaml"
)

# Default log path
DEFAULT_LOGS_DIR = r"H:/Logs"

# Processing settings
DEFAULT_PROCESSED_MEDIA_MAX_COUNT = 1
DEFAULT_INTERVAL = 10

# AI configuration file path
AI_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "ai_config.json")
DEFAULT_TRAINING_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training")
# Neural network settings
DEFAULT_TRAINING_ITERATIONS = 10  # Default number of iterations for training after each file
DEFAULT_TRAINING_BATCH_SIZE = 32
DEFAULT_TRAINING_LEARNING_RATE = 0.001
DEFAULT_TRAINING_EPOCHS = 5

# LLM settings
DEFAULT_LLM_TIMEOUT = 30  # seconds
DEFAULT_LLM_MAX_TOKENS = 1000

# JSON response structures
TITLE_JSON_STRUCTURE = {"title": "string"}  # The generated title, max 80 characters

DESCRIPTION_JSON_STRUCTURE = {"description": "string"}  # The generated description, max 200 characters

KEYWORDS_JSON_STRUCTURE = {"keywords": ["string"]}  # List of 10-20 keywords as strings

CATEGORY_JSON_STRUCTURE = {"category": "string"}  # The selected category name from the provided list

ALL_METADATA_JSON_STRUCTURE = {
    "title": "string",  # The generated title
    "description": "string",  # The generated description
    "keywords": ["string"],  # List of keywords
    "category": "string",  # The selected category
}

# Prompts for LLM
TITLE_PROMPT = """Generate a concise, descriptive title for this image that would be suitable for a stock photo website.
The title should be clear, specific, and under 80 characters.
Describe the main subject and context without using unnecessary adjectives.
Do not use phrases like "stock photo" or "image of" in the title.

You MUST respond with a valid JSON object with the following structure:
{"title": "Your generated title here"}
"""

DESCRIPTION_PROMPT = """Write a detailed description for this image for a stock photo website.
The description should be factual, specific, and under 200 characters.
Include the main subject, setting, action, and mood if relevant.
Do not use phrases like "stock photo" or "image shows" in the description.

You MUST respond with a valid JSON object with the following structure:
{"description": "Your generated description here"}
"""

KEYWORDS_PROMPT = """Generate a list of relevant keywords for this image for a stock photo website.
Include specific objects, concepts, actions, emotions, and settings visible in the image.
Provide 10-20 keywords, separated by commas.
Include both specific and general terms to maximize searchability.
Do not include redundant or overly similar keywords.

You MUST respond with a valid JSON object with the following structure:
{"keywords": ["keyword1", "keyword2", "keyword3", ... ]}
"""

CATEGORIES_PROMPT = """Based on the image content, select the most appropriate category from the following list:
{categories}

You MUST respond with a valid JSON object with the following structure:
{"category": "The exact category name from the list"}
"""

ALL_METADATA_PROMPT = """Generate complete metadata for this image for a stock photo website.

1. Title: Generate a concise, descriptive title under 80 characters.
2. Description: Write a detailed description under 200 characters.
3. Keywords: Provide 10-20 relevant keywords.
4. Category: Select the most appropriate category from this list: {categories}

You MUST respond with a valid JSON object with the following structure:
{
  "title": "Your generated title",
  "description": "Your generated description",
  "keywords": ["keyword1", "keyword2", "keyword3", ...],
  "category": "The exact category name from the list"
}
"""
