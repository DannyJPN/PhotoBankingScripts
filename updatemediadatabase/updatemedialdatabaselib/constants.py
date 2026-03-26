"""
Constants for the UpdateMediaDatabase project.
Contains default paths and configuration values.
"""

# Default paths for CSV files (consistent with givephotobankreadymediafiles)
DEFAULT_MEDIA_CSV_PATH = r"L:\Můj disk\XLS\Fotobanky\PhotoMedia.csv"
DEFAULT_LIMITS_CSV_PATH = r"L:\Můj disk\XLS\Fotobanky\PhotoLimits.csv"

# Default media directories
DEFAULT_PHOTO_DIR = "J:/Foto"
DEFAULT_VIDEO_DIR = "J:/Video"
DEFAULT_EDIT_PHOTO_DIR = "J:/Upravené foto"
DEFAULT_EDIT_VIDEO_DIR = "J:/Upravené video"

# Default tool and log directories
DEFAULT_LOG_DIR = "H:/Logs"

# ExifTool path (consistent with other scripts)
EXIFTOOL_PATH = "F:/Dropbox/exiftool-12.30/exiftool.exe"

# Media file extensions (consistent with givephotobankreadymediafiles)
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.dng', '.nef', '.raw', '.cr2', '.arw', '.psd']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.wmv', '.mkv']
VECTOR_EXTENSIONS = ['.svg', '.eps', '.ai']

# CSV column names (Czech - matching PhotoMedia.csv structure)
COLUMN_FILENAME = "Soubor"
COLUMN_PATH = "Cesta"
COLUMN_TITLE = "Název"
COLUMN_DESCRIPTION = "Popis"
COLUMN_DATE_PREPARED = "Datum přípravy"
COLUMN_WIDTH = "Šířka"
COLUMN_HEIGHT = "Výška"
COLUMN_RESOLUTION = "Rozlišení"
COLUMN_KEYWORDS = "Klíčová slova"
COLUMN_CATEGORIES = "Kategorie"
COLUMN_DATE_CREATED = "Datum vytvoření"
COLUMN_ORIGINAL = "Originál"

# Photo bank status columns
# Active banks
COLUMN_SHUTTERSTOCK_STATUS = "ShutterStock status"
COLUMN_ADOBESTOCK_STATUS = "AdobeStock status"
COLUMN_DEPOSITPHOTOS_STATUS = "DepositPhotos status"
COLUMN_123RF_STATUS = "123RF status"
COLUMN_ALAMY_STATUS = "Alamy status"
COLUMN_GETTYIMAGES_STATUS = "GettyImages status"
COLUMN_DREAMSTIME_STATUS = "Dreamstime status"
COLUMN_POND5_STATUS = "Pond5 status"
# Deprecated banks (kept for historical data)
COLUMN_BIGSTOCKPHOTO_STATUS = "BigStockPhoto status"
COLUMN_CANSTOCKPHOTO_STATUS = "CanStockPhoto status"
COLUMN_COLOURBOX_STATUS = "ColourBox status"
# New banks
COLUMN_PIXTA_STATUS = "Pixta status"
COLUMN_FREEPIK_STATUS = "Freepik status"
COLUMN_VECTEEZY_STATUS = "Vecteezy status"
COLUMN_STORYBLOCKS_STATUS = "StoryBlocks status"
COLUMN_ENVATO_STATUS = "Envato status"
COLUMN_500PX_STATUS = "500px status"
COLUMN_MOSTPHOTOS_STATUS = "MostPhotos status"

# Photo bank category columns
# Active banks
COLUMN_SHUTTERSTOCK_CATEGORY = "ShutterStock kategorie"
COLUMN_ADOBESTOCK_CATEGORY = "AdobeStock kategorie"
COLUMN_DEPOSITPHOTOS_CATEGORY = "DepositPhotos kategorie"
COLUMN_123RF_CATEGORY = "123RF kategorie"
COLUMN_ALAMY_CATEGORY = "Alamy kategorie"
COLUMN_GETTYIMAGES_CATEGORY = "GettyImages kategorie"
COLUMN_DREAMSTIME_CATEGORY = "Dreamstime kategorie"
COLUMN_POND5_CATEGORY = "Pond5 kategorie"
# Deprecated banks (kept for historical data)
COLUMN_BIGSTOCKPHOTO_CATEGORY = "BigStockPhoto kategorie"
COLUMN_CANSTOCKPHOTO_CATEGORY = "CanStockPhoto kategorie"
COLUMN_COLOURBOX_CATEGORY = "ColourBox kategorie"
# New banks
COLUMN_PIXTA_CATEGORY = "Pixta kategorie"
COLUMN_FREEPIK_CATEGORY = "Freepik kategorie"
COLUMN_VECTEEZY_CATEGORY = "Vecteezy kategorie"
COLUMN_STORYBLOCKS_CATEGORY = "StoryBlocks kategorie"
COLUMN_ENVATO_CATEGORY = "Envato kategorie"
COLUMN_500PX_CATEGORY = "500px kategorie"
COLUMN_MOSTPHOTOS_CATEGORY = "MostPhotos kategorie"

# PhotoLimits.csv column names
LIMITS_COLUMN_BANK = "Banka"
LIMITS_COLUMN_WIDTH = "šířka"
LIMITS_COLUMN_HEIGHT = "výška"
LIMITS_COLUMN_RESOLUTION = "rozlišení"
LIMITS_COLUMN_MEDIA_TYPE = "typ"

# Media types
TYPE_PHOTO = "Photo"
TYPE_VIDEO = "Video"
TYPE_VECTOR = "Vector"
TYPE_EDITED_PHOTO = "EditedPhoto"
TYPE_EDITED_VIDEO = "EditedVideo"
TYPE_EDITED_VECTOR = "EditedVector"

# Status values (Czech - matching PhotoMedia.csv values)
STATUS_PREPARED = "připraveno"
STATUS_UNPROCESSED = "nezpracováno"
STATUS_REJECTED_SIZE = "zamítnuto - velikost"
STATUS_REJECTED = "zamítnuto"
STATUS_UNAVAILABLE = "nedostupné"

# File numbering system constants
MIN_NUMBER_WIDTH = 4  # Minimum width for backward compatibility with existing files
MAX_NUMBER_WIDTH = 6  # Maximum width for new capacity
DEFAULT_NUMBER_WIDTH = 6  # Default width for new file generation
MAX_NUMBER = 999999  # Maximum number with 6 digits
