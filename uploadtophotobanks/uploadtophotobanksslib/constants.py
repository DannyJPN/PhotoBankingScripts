"""
Constants for the photobank upload system.
"""
import os

# Status constants
STATUS_PREPARED = "připraveno"
STATUS_UPLOADED = "nahráno"
STATUS_FAILED = "chyba"
STATUS_REJECTED = "zamítnuto"

# Upload protocols
PROTOCOL_FTP = "ftp"
PROTOCOL_FTPS = "ftps"
PROTOCOL_SFTP = "sftp"
PROTOCOL_HTTP = "http"
PROTOCOL_HTTPS = "https"

# File types
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.dng', '.nef', '.raw', '.cr2', '.arw']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.wmv', '.mkv']
VECTOR_EXTENSIONS = ['.svg', '.eps', '.ai']

# CSV column names
COL_FILE = "Soubor"
COL_TITLE = "Název"
COL_DESCRIPTION = "Popis"
COL_PREP_DATE = "Datum přípravy"
COL_UPLOAD_DATE = "Datum nahrání"
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

# Photobank configuration (based on documentation analysis)
PHOTOBANK_CONFIGS = {
    "ShutterStock": {
        "protocol": "ftps",
        "host": "ftps.shutterstock.com",
        "port": 21,
        "passive": True,
        "explicit_tls": True,
        "directory": "/",
        "supported_formats": ['.jpg', '.eps', '.tiff', '.mp4', '.mov'],
        "min_mp": 4,
        "max_file_size": {"jpg": 50*1024*1024, "eps": 100*1024*1024, "tiff": 4*1024*1024*1024}
    },
    "Pond5": {
        "protocol": "ftp",
        "host": "ftp.pond5.com",
        "port": 21,
        "passive": True,
        "directory": "/",
        "release_directory": "/Release",
        "supported_formats": ['.jpg', '.mp4', '.mov', '.wav', '.eps'],
        "min_mp": 4,
        "max_file_size": {"default": 4*1024*1024*1024}
    },
    "123RF": {
        "protocol": "ftp",
        "hosts": {
            "photos": "ftp.123rf.com",
            "video": "footage.ftp.123rf.com",
            "audio": "audio.ftp.123rf.com"
        },
        "port": 21,
        "passive": True,
        "directory": "/",
        "quota": {"photos": 4*1024*1024*1024, "video": 30*1024*1024*1024},
        "supported_formats": ['.jpg', '.eps', '.mp4', '.mp3'],
        "min_mp": 6
    },
    "DepositPhotos": {
        "protocol": "ftp",
        "host": "ftp.depositphotos.com",
        "port": 21,
        "passive": True,
        "directory": "/",
        "supported_formats": ['.jpg', '.zip'],  # vectors as ZIP(eps+jpg)
        "min_mp": 3.4,
        "max_file_size": {"jpg": 50*1024*1024}
    },
    "Alamy": {
        "protocol": "ftp",
        "host": "upload.alamy.com",
        "port": 21,
        "passive": True,
        "directories": {
            "stock": "/Stock",
            "live_news": "/Live News",
            "archive": "/Archive stock",
            "vectors": "/Vectors"
        },
        "supported_formats": ['.jpg', '.tiff', '.eps'],
        "min_mp": 6
    },
    "Dreamstime": {
        "protocol": "ftp",
        "host": "upload.dreamstime.com",
        "port": 21,
        "passive": True,
        "directories": {
            "photos": "/",
            "additional": "/additional",
            "video": "/video",
            "audio": "/audio",
            "releases": "/modelrelease"
        },
        "supported_formats": ['.jpg', '.eps', '.mov', '.mp4', '.wav'],
        "min_mp": 3
    },
    "AdobeStock": {
        "protocol": "sftp",
        "host": "sftp.contributor.adobestock.com",
        "port": 22,
        "directory": "/",
        "supported_formats": ['.jpg', '.ai', '.eps', '.mp4', '.mov'],
        "min_mp": 4,
        "max_file_size": {"jpg": 45*1024*1024, "video": 4*1024*1024*1024},
        "requires_qualification": True
    },
    "CanStockPhoto": {
        "protocol": "discontinued",
        "host": None,
        "port": None,
        "directory": None,
        "supported_formats": [],
        "discontinued": True,
        "discontinued_date": "2024",
        "discontinuation_message": "CanStockPhoto has been discontinued and is no longer accepting uploads."
    },
    "BigStockPhoto": {
        "protocol": "discontinued",
        "host": None,
        "port": None,
        "directory": None,
        "supported_formats": [],
        "discontinued": True,
        "discontinued_date": "2024",
        "discontinuation_message": "BigStockPhoto has been deprecated."
    },
    # New banks
    "Freepik": {
        "protocol": "sftp",
        "host": "contributor-ftp.freepik.com",
        "port": 60022,
        "directory": "/",
        "supported_formats": ['.jpg', '.eps', '.psd'],
        "requires_level": 3,
        "requires_published_files": 500,
        "min_mp": 3,
        "note": "Requires Level 3 contributor status (500+ published files)"
    },
    "MostPhotos": {
        "protocol": "ftp",
        "host": None,  # Obtain from contributor dashboard
        "port": 21,
        "directory": "/",
        "directories": {
            "photos": "/",
            "vectors": "/vectorimages"
        },
        "supported_formats": ['.jpg', '.eps', '.ai'],
        "note": "FTP credentials must be obtained from contributor dashboard or support@mostphotos.com"
    },
    # Web-only banks (no FTP/SFTP upload support)
    "Pixta": {
        "protocol": "web",
        "upload_method": "csv",
        "supported_formats": ['.jpg', '.png', '.eps'],
        "note": "CSV metadata upload via web interface"
    },
    "Vecteezy": {
        "protocol": "web",
        "upload_method": "manual",
        "supported_formats": ['.jpg', '.eps'],
        "note": "Web upload only"
    },
    "StoryBlocks": {
        "protocol": "web",
        "upload_method": "portal",
        "supported_formats": ['.mov', '.mp4'],
        "note": "Contributor portal upload only"
    },
    "Envato": {
        "protocol": "web",
        "upload_method": "portfolio_manager",
        "supported_formats": ['.jpg'],
        "note": "Portfolio Manager upload (IPTC metadata only)"
    },
    "500px": {
        "protocol": "web",
        "upload_method": "manual",
        "supported_formats": ['.jpg'],
        "note": "Web upload only (API deprecated 2018)"
    }
}

# Connection settings
DEFAULT_TIMEOUT = 300  # 5 minutes
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 5  # seconds

# FTP settings
DEFAULT_FTP_PORT = 21
DEFAULT_FTPS_PORT = 990
DEFAULT_SFTP_PORT = 22

# Upload chunk size (in bytes)
DEFAULT_CHUNK_SIZE = 8192  # 8KB

# Base directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Default paths
DEFAULT_PHOTO_CSV = r"L:\Můj disk\XLS\Fotobanky\PhotoMedia.csv"
DEFAULT_PROCESSED_MEDIA_FOLDER = r"L:\Můj disk\PhotoBankMedia"  # Where createbatch copies files
DEFAULT_EXPORT_DIR = r"L:\Můj disk\XLS\Fotobanky\CSV"
DEFAULT_LOG_DIR = r"H:\Logs"

# Credentials configuration paths
DEFAULT_CREDENTIALS_FILE = os.path.join(BASE_DIR, "config", "credentials.json")
DEFAULT_BANK_CONFIG_FILE = os.path.join(BASE_DIR, "config", "bank_configs.json")

# Upload result constants
UPLOAD_SUCCESS = "success"
UPLOAD_FAILURE = "failure"
UPLOAD_PARTIAL = "partial"
UPLOAD_SKIPPED = "skipped"

# Progress tracking
DEFAULT_PROGRESS_UPDATE_INTERVAL = 100  # Update progress every N files

# Logging constants
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Valid status for upload
VALID_STATUS_FOR_UPLOAD = "připraveno"