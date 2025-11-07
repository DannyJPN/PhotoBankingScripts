import os
import sys

# Add parent directory to path to import shared modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from shared.user_config import get_username, get_author, get_location

# Výchozí hodnoty pro vstupní a výstupní soubory
DEFAULT_PHOTO_CSV = r"L:\Můj disk\XLS\Fotobanky\PhotoMedia.csv"
DEFAULT_OUTPUT_DIR = r"L:\Můj disk\XLS\Fotobanky\CSV"
DEFAULT_OUTPUT_PREFIX = "CSV"

# Výchozí hodnoty pro metadata (loaded from user config or environment variables)
# To configure, either:
# 1. Set environment variables: PHOTOBANK_USERNAME, PHOTOBANK_AUTHOR, PHOTOBANK_LOCATION
# 2. Create user.config.json file (see user.template.json)
# 3. Create ~/.photobanking/user.json file
DEFAULT_LOCATION = get_location()
DEFAULT_USERNAME = get_username()
DEFAULT_COPYRIGHT_AUTHOR = get_author()

# Cesty k mapám kategorií
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ADOBE_CATEGORY_PATH = os.path.join(BASE_DIR, "exportpreparedmedialib", "data", "adobe_stock_categories.csv")
DEFAULT_DREAMSTIME_CATEGORY_PATH = os.path.join(BASE_DIR, "exportpreparedmedialib", "data", "dreams_time_categories.csv")

# Cesty k CSV souborům pro exporty
DEFAULT_PHOTOBANK_EXPORT_FORMATS_PATH = os.path.join(BASE_DIR, "exportpreparedmedialib", "data", "photobank_export_formats.csv")
DEFAULT_POND_PRICES_PATH = os.path.join(BASE_DIR, "exportpreparedmedialib", "data", "pond_prices.csv")

# Regulární výrazy pro detekci typů souborů
EDITORIAL_REGEX = r"^[A-Za-z]{1,}, [A-Za-z]{1,} - \d{2} \d{2} \d{4}:"
VECTOREXT_REGEX = r"(cdr|ai|eps|svg)$"

# Validní hodnota pro status
VALID_STATUS = "připraveno"

# Default log directory
DEFAULT_LOG_DIR = "H:/Logs"

# RAW image formats
RAW_FORMATS = {
    '.raw', '.nef', '.arw', '.pmp', '.srf', '.crw', '.cr2', '.cr3',
    '.cmt', '.dcr', '.dng', '.j6i', '.mos', '.mrw', '.orf', '.pef',
    '.raf', '.x3f', '.rw2'
}

# Supported image formats by photobank
PHOTOBANK_SUPPORTED_FORMATS = {
    'DreamsTime': {'.jpg', '.png'} | RAW_FORMATS,
    'Pond5': {'.jpg', '.png', '.tif'},
    'ShutterStock': {'.jpg'},
    'AdobeStock': {'.jpg'},
    'GettyImages': {'.jpg'},
    '123RF': {'.jpg'},
    'DepositPhotos': {'.jpg', '.png'},
    'Alamy': {'.jpg'},
    'BigStockPhoto': {'.jpg'},
    'CanStockPhoto': {'.jpg'},
}

# Format subdirectory names (for finding files in parallel directories)
FORMAT_SUBDIRS = {
    '.jpg': 'JPG',
    '.png': 'PNG',
    '.tif': 'TIF',
    **{ext: 'RAW' for ext in RAW_FORMATS}
}

# File numbering system constants
MIN_NUMBER_WIDTH = 4  # Minimum width for backward compatibility with existing files
MAX_NUMBER_WIDTH = 6  # Maximum width for new capacity
DEFAULT_NUMBER_WIDTH = 6  # Default width for new file generation
MAX_NUMBER = 999999  # Maximum number with 6 digits