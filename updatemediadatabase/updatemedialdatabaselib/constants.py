"""
Constants for the UpdateMediaDatabase project.
Contains default paths and configuration values.
"""

# Default paths for CSV files
DEFAULT_PHOTO_CSV = "L:/Můj disk/XLS/Fotobanky/PhotoMedia.csv"
DEFAULT_LIMIT_CSV = "L:/Můj disk/XLS/Fotobanky/PhotoLimits.csv"

# Default media directories
DEFAULT_PHOTO_DIR = "J:/Foto"
DEFAULT_VIDEO_DIR = "J:/Video"
DEFAULT_EDIT_PHOTO_DIR = "J:/Upravené foto"
DEFAULT_EDIT_VIDEO_DIR = "J:/Upravené video"

# Default tool and log directories
DEFAULT_LOG_DIR = "H:/Logs"
DEFAULT_EXIFTOOL_DIR = "H:/Tools/ExifTool"

# Media file extensions
PHOTO_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp', '.webp']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.webm']

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

# Media types
TYPE_PHOTO = "Photo"
TYPE_VIDEO = "Video"
TYPE_EDITED_PHOTO = "EditedPhoto"
TYPE_EDITED_VIDEO = "EditedVideo"
