# File: exportpreparedmedialib/constants.py

# Default file paths
PHOTO_CSV_FILE_DEFAULT = r"F:\Disk Google (krupadan.jp@gmail.com)\XLS\Fotobanky/PhotoMediaTest.csv"
CSV_LOCATION_DEFAULT = r"F:\Disk Google (krupadan.jp@gmail.com)\XLS\Fotobanky\CSV"
LOG_DIR = r"H:/Logs"
CATEGORY_CSV_DIR = r"./config"  # New constant for category CSV directory

# Status strings
STATUS_READY = "připraveno"
STATUS_CHECKED = "kontrolováno"

# Headers for photobank CSVs
PHOTOBANK_HEADERS = ["KEY", "VALUE"]

# Photobank names
SHUTTERSTOCK = "ShutterStock"
ADOBE_STOCK = "AdobeStock"
DREAMS_TIME = "Dreamstime"
DEPOSIT_PHOTOS = "DepositPhotos"
BIG_STOCK_PHOTO = "BigStockPhoto"
RF_123 = "123RF"
CAN_STOCK_PHOTO = "CanStockPhoto"
POND5 = "Pond5"
ALAMY = "Alamy"
GETTY_IMAGES = "GettyImages"

# List of photobanks
PHOTOBANKS = [
    SHUTTERSTOCK,
    ADOBE_STOCK,
    DREAMS_TIME,
    DEPOSIT_PHOTOS,
    BIG_STOCK_PHOTO,
    RF_123,
    CAN_STOCK_PHOTO,
    POND5,
    ALAMY,
    GETTY_IMAGES
]

# Editorial regex pattern
EDITORIAL_REGEX = r"^[A-Za-z]{1,}, [A-Za-z]{1,} - [0-9]{2} [0-9]{2} [0-9]{4}:"

# File extension lists
VIDEO_EXTENSIONS_FILE = "config/video_extensions.txt"
IMAGE_EXTENSIONS_FILE = "config/image_extensions.txt"
ILLUSTRATION_EXTENSIONS_FILE = "config/illustration_extensions.txt"

# Not Available constant
NA = "NA"

# Constant values
LOCATION = "Czech republic"
MATURE_CONTENT = "no"
FREE = "0"
W_EL = "1"
P_EL = "1"
SR_EL = "0"
SR_PRICE = "0"
MR_DOC_IDS = "0"
PR_DOCS = "0"
NUDITY = "no"
COUNTRY = "CZ"
SPECIFY_SOURCE = ""
USERNAME = "DannyJPN"
EXCLUSIVE = "N"
ADDITIONAL_INFO = ""
NA_VALUE = "NA"

# New constants for additional file extensions
VECTOR_FILE_EXTENSIONS = ['tif', 'tiff']
# Define delimiters for different photobanks
DELIMITERS = {
    "CanStockPhoto": "\t",  # Tab-separated
    "default": ","          # Default comma-separated
}
