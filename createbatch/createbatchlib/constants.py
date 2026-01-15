
DEFAULT_PHOTO_CSV_FILE = "L:/Můj disk/XLS/Fotobanky/PhotoMedia.csv"
DEFAULT_PROCESSED_MEDIA_FOLDER = "L:/Můj disk/PhotoBankMedia"
DEFAULT_LOG_DIR = "H:/Logs"
STATUS_FIELD_KEYWORD = "status"
PREPARED_STATUS_VALUE = "připraveno"

# ExifTool path
EXIFTOOL_PATH = "F:/Dropbox/exiftool-12.30/exiftool.exe"

# RAW image formats
RAW_FORMATS = {
    '.raw',  # Generic RAW
    '.nef',  # Nikon
    '.arw', '.pmp', '.srf',  # Sony
    '.crw', '.cr2', '.cr3',  # Canon
    '.cmt',  # Chinon
    '.dcr',  # Kodak
    '.dng',  # Digital Negative
    '.j6i',  # Ricoh
    '.mos',  # Leaf Valeo
    '.mrw',  # Minolta
    '.orf',  # Olympus
    '.pef',  # Pentax
    '.raf',  # Fuji
    '.x3f',  # Sigma
    '.rw2',  # Panasonic Lumix
}

# Supported image formats by photobank (photos, videos, vectors)
PHOTOBANK_SUPPORTED_FORMATS = {
    # Active banks
    'ShutterStock': {'.jpg', '.tif', '.mov', '.mp4', '.eps'},
    'AdobeStock': {'.jpg', '.mov', '.mpg', '.mp4', '.ai', '.eps'},
    'Dreamstime': {'.jpg', '.mov', '.avi', '.mp4', '.mpeg', '.wmv', '.cdr', '.ai', '.eps', '.png', '.svg'} | RAW_FORMATS,
    'DepositPhotos': {'.jpg', '.png', '.asf', '.mp4', '.ai', '.eps'},
    'GettyImages': {'.jpg', '.eps'},
    'Pond5': {'.jpg', '.tif', '.png', '.mov', '.mp4', '.eps'},
    'Alamy': {'.jpg', '.eps'},
    '123RF': {'.jpg', '.mov', '.wmv', '.mp4', '.avi', '.m2ts', '.eps'},
    # Deprecated banks
    'BigStockPhoto': {'.jpg'},
    'CanStockPhoto': {'.jpg'},
    # New banks
    'Pixta': {'.jpg', '.png', '.eps'},
    'Freepik': {'.jpg', '.eps', '.psd'},
    'Vecteezy': {'.jpg', '.eps'},
    'StoryBlocks': {'.mov', '.mp4'},
    'Envato': {'.jpg'},
    '500px': {'.jpg'},
    'MostPhotos': {'.jpg', '.eps', '.ai'},
}

# Format subdirectory names
FORMAT_SUBDIRS = {
    '.jpg': 'jpg',
    '.png': 'png',
    '.tif': 'tif',
    **{ext: 'raw' for ext in RAW_FORMATS}
}

# Alternative edit tags (from givephotobankreadymediafiles)
ALTERNATIVE_EDIT_TAGS = {
    "_bw": "Black and white",
    "_negative": "Color negative",
    "_sharpen": "Sharpened",
    "_misty": "Misty/foggy effect",
    "_blurred": "Gaussian blur"
}

# Editorial content detection
EDITORIAL_REGEX = r"^[A-Za-z]{1,}, [A-Za-z]{1,} - \d{2} \d{2} \d{4}:"

# Banks that do NOT accept editorial content
# Editorial files will be automatically excluded from batch creation for these banks
BANKS_NO_EDITORIAL = {
    'AdobeStock',   # Commercial content only
    'GettyImages',  # Separate editorial portal
    'Freepik',      # Commercial content only
    'Pixta',        # Commercial content only
}

# Batch size limits for photobanks (items per batch)
# Banks not listed here have no batch size limit
PHOTOBANK_BATCH_SIZE_LIMITS = {
    'GettyImages': 128,
}