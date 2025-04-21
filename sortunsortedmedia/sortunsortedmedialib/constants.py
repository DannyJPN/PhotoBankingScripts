"""
Constants for the SortUnsortedMedia project.
Contains default values, regular expressions, and dictionaries for media classification.
"""

# Default folder paths
DEFAULT_UNSORTED_FOLDER = "I:/Neroztříděno"
DEFAULT_TARGET_FOLDER = "I:/Roztříděno"
DEFAULT_INTERVAL = 3600  # seconds

# Tags indicating edited files
EDITED_TAGS = {
    "_bw": "Blackwhite",
    "_crop": "Cropped",
    "_sharpen": "Sharpened",
    "_edit": "Edited",
    "_hdr": "HDR",
    "_pano": "Panorama",
    "_fix": "Fixed",
    "_retouch": "Retouched",
    "_color": "Colorized",
    "_denoise": "Denoised",
    "_enhance": "Enhanced",
    "_filter": "Filtered",
    "_collage": "Collage"
}

# Regular expressions for camera detection
CAMERA_REGEXES = {
    r"^DSC\d{5}$": "Sony CyberShot W810",
    r"^IMG\d{14}$": "Realme 8",
    r"^IMG_\d{4}$": "iPhone",
    r"^P\d{7}$": "Nikon P900",
    r"^DJI_\d{4}$": "DJI Drone",
    r"^PANO_\d{8}$": "Panorama App",
    r"^DCIM\d{4}$": "Canon EOS",
    r"^DSCF\d{4}$": "Fujifilm",
    r"^PICT\d{4}$": "Generic Camera",
    r"^MVI_\d{4}$": "Canon Video",
    r"^M\d{3}$": "GoPro",
    r"^100GOPRO$": "GoPro",
    r"^GOPR\d{4}$": "GoPro"
}

# File extensions and their media types
EXTENSION_TYPES = {
    # Photos
    "jpg": "Foto",
    "jpeg": "Foto",
    "png": "Foto",
    "gif": "Foto",
    "bmp": "Foto",
    "tiff": "Foto",
    "tif": "Foto",
    "webp": "Foto",
    "heic": "Foto",
    "heif": "Foto",
    "raw": "Foto",
    "arw": "Foto",
    "cr2": "Foto",
    "cr3": "Foto",
    "nef": "Foto",
    "orf": "Foto",
    "rw2": "Foto",
    "dng": "Foto",
    
    # Videos
    "mp4": "Video",
    "mov": "Video",
    "avi": "Video",
    "wmv": "Video",
    "flv": "Video",
    "mkv": "Video",
    "webm": "Video",
    "m4v": "Video",
    "3gp": "Video",
    "mpg": "Video",
    "mpeg": "Video",
    "mts": "Video",
    "m2ts": "Video"
}

# Categories for organizing media
DEFAULT_CATEGORIES = [
    "Rodina",
    "Příroda",
    "Město",
    "Architektura",
    "Zvířata",
    "Cestování",
    "Jídlo",
    "Akce",
    "Práce",
    "Ostatní"
]

# Folder structure format strings
DATE_FORMAT = "%Y-%m-%d"
FOLDER_STRUCTURE = {
    "Foto": "{year}/{month}/{date}_{category}_{camera}",
    "Video": "Video/{year}/{month}/{date}_{category}_{camera}",
    "Edited": "Upravené/{year}/{month}/{date}_{category}_{camera}_{edit_type}"
}
