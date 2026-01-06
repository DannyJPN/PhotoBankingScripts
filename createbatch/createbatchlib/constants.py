DEFAULT_PHOTO_CSV_FILE = "L:/MĹŻj disk/XLS/Fotobanky/PhotoMedia.csv"
DEFAULT_PROCESSED_MEDIA_FOLDER = "L:/MĹŻj disk/PhotoBankMedia"
DEFAULT_LOG_DIR = "H:/Logs"
STATUS_FIELD_KEYWORD = "status"
PREPARED_STATUS_VALUE = "pĹ™ipraveno"`nPREPARED_DATE_COLUMN = "Datum přípravy"

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

# Supported image formats by photobank
PHOTOBANK_SUPPORTED_FORMATS = {
    'Dreamstime': {'.jpg', '.png'} | RAW_FORMATS,
    'Pond5': {'.jpg', '.png', '.tif'},
    'Shutterstock': {'.jpg'},
    'Adobe Stock': {'.jpg'},
    'Getty Images': {'.jpg'},
    '123RF': {'.jpg'},
    'Depositphotos': {'.jpg', '.png'},
    'Alamy': {'.jpg'},
    'Bigstock': {'.jpg'},
    'CanStockPhoto': {'.jpg'},
    'iStock': {'.jpg'},
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

# Batch size limits for photobanks (items per batch)
# Banks not listed here have no batch size limit
PHOTOBANK_BATCH_SIZE_LIMITS = {
    'Getty Images': 128,  # Note: Inconsistent naming with export ('GettyImages')
}
