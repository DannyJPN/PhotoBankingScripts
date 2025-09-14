"""
Constants for the UpdateMediaDatabase project.
Contains default paths and configuration values.
"""

# Default paths for CSV files (consistent with givephotobankreadymediafiles)
DEFAULT_MEDIA_CSV_PATH = r"L:\Můj disk\XLS\Fotobanky\PhotoMediaTest.csv"
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
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.dng', '.nef', '.raw', '.cr2', '.arw']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.wmv', '.mkv']
VECTOR_EXTENSIONS = ['.svg', '.eps', '.ai']

# CSV column names
COLUMN_FILENAME = "Filename"
COLUMN_PATH = "Path"
COLUMN_TYPE = "Type"
COLUMN_WIDTH = "Width"
COLUMN_HEIGHT = "Height"
COLUMN_SIZE = "Size"
COLUMN_DATE = "Date"
COLUMN_TITLE = "Title"
COLUMN_DESCRIPTION = "Description"
COLUMN_KEYWORDS = "Keywords"
COLUMN_ORIGINAL = "Original"
COLUMN_EDIT_TYPE = "EditType"
COLUMN_CAMERA = "Camera"
COLUMN_LENS = "Lens"
COLUMN_FOCAL_LENGTH = "FocalLength"
COLUMN_APERTURE = "Aperture"
COLUMN_SHUTTER = "Shutter"
COLUMN_ISO = "ISO"

# PhotoLimits.csv column names
LIMITS_COLUMN_BANK = "Banka"
LIMITS_COLUMN_WIDTH = "šířka"
LIMITS_COLUMN_HEIGHT = "výška" 
LIMITS_COLUMN_RESOLUTION = "rozlišení"

# Media types
TYPE_PHOTO = "Photo"
TYPE_VIDEO = "Video"
TYPE_EDITED_PHOTO = "EditedPhoto"
TYPE_EDITED_VIDEO = "EditedVideo"
