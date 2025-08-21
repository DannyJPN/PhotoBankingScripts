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

# Regular expressions for camera detection based on actual file patterns found on J: drive
CAMERA_REGEXES = {
    # Sony CyberShot W810 - DSC00151.JPG pattern (verified from J: analysis)
    r"^DSC\d{5}$": "Sony CyberShot W810",
    
    # Realme 8 - IMG20220423105358.jpg pattern (verified from J: analysis)
    r"^IMG\d{14}$": "Realme 8",
    
    # Samsung J320FN - 20210729_141633.jpg pattern (verified from J: analysis)
    r"^\d{8}_\d{6}$": "Samsung J320FN",
    
    # Samsung ES9 - older Samsung camera patterns (verified from J: analysis)
    r"^SAM_\d{4}$": "Samsung ES9",
    
    # Nikon Z50 - NIK_1797.JPG, NIK_2833.NEF patterns (verified from J: analysis)
    r"^NIK_\d{4}$": "Nikon Z50",
    
    # DJI Drone patterns (from error message: DJI_20250402140705_0008_W.JPG)
    r"^DJI_\d{14}_\d{4}_[WTZN]$": "DJI Drone",
    r"^DJI_\d{4}$": "DJI Drone",
    
    # Other camera patterns (keeping existing for compatibility)
    # Bunaty Micro 4K - PICT0195.JPG pattern
    r"^PICT\d{4}$": "Bunaty Micro 4K",
    
    # Bunaty WiFi Solar - 20240914051558_IM_01008.JPG pattern
    r"^\d{14}_IM_\d{5}$": "Bunaty WiFi Solar",
    
    # Acer 10 - WIN_20180226_07_01_04_Pro.jpg pattern
    r"^WIN_\d{8}_\d{2}_\d{2}_\d{2}_Pro$": "Acer 10",
    
    # Generic phone patterns
    r"^IMG_\d{4}$": "Generic Phone",
    r"^IMG-\d{8}-WA\d{4}$": "WhatsApp",
    r"^VID-\d{8}-WA\d{4}$": "WhatsApp Video",
    
    # Screenshot patterns
    r"^Screenshot_\d{8}-\d{6}$": "Screenshot",
    r"^Screen_Shot_\d{4}-\d{2}-\d{2}_at_\d{2}\.\d{2}\.\d{2}$": "Screenshot",
    r"^screenshot_\d+$": "Screenshot"
}

# File extensions and their media types - extended for maximum format support
EXTENSION_TYPES = {
    # Photos - Standard formats
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
    "avif": "Foto",
    "jxl": "Foto",  # JPEG XL
    
    # Photos - RAW formats (comprehensive list)
    "raw": "Foto",
    "dng": "Foto",  # Adobe Digital Negative
    "arw": "Foto",  # Sony
    "srf": "Foto",  # Sony
    "sr2": "Foto",  # Sony
    "cr2": "Foto",  # Canon
    "cr3": "Foto",  # Canon
    "crw": "Foto",  # Canon
    "nef": "Foto",  # Nikon
    "nrw": "Foto",  # Nikon
    "orf": "Foto",  # Olympus
    "rw2": "Foto",  # Panasonic
    "raw": "Foto",  # Panasonic
    "rwl": "Foto",  # Leica
    "dcs": "Foto",  # Kodak
    "dcr": "Foto",  # Kodak
    "kdc": "Foto",  # Kodak
    "erf": "Foto",  # Epson
    "mef": "Foto",  # Mamiya
    "mrw": "Foto",  # Minolta
    "pef": "Foto",  # Pentax
    "ptx": "Foto",  # Pentax
    "r3d": "Foto",  # RED
    "raf": "Foto",  # Fuji
    "x3f": "Foto",  # Sigma
    "3fr": "Foto",  # Hasselblad
    "fff": "Foto",  # Imacon
    "iiq": "Foto",  # Phase One
    "k25": "Foto",  # Kodak
    "bay": "Foto",  # Casio
    "cap": "Foto",  # Phase One
    "data": "Foto", # Pentax
    "drf": "Foto",  # Kodak
    "eip": "Foto",  # Phase One
    "gpr": "Foto",  # GoPro
    
    # Photos - Photoshop and professional formats
    "psd": "Foto",  # Photoshop Document
    "psb": "Foto",  # Large Photoshop Document
    "xcf": "Foto",  # GIMP
    "ai": "Foto",   # Adobe Illustrator
    "eps": "Foto",  # Encapsulated PostScript
    "svg": "Foto",  # Scalable Vector Graphics
    "svgz": "Foto", # Compressed SVG
    "pdf": "Foto",  # Portable Document Format (can contain images)
    
    # Videos - Standard formats
    "mp4": "Video",
    "mov": "Video",
    "avi": "Video",
    "wmv": "Video",
    "flv": "Video",
    "mkv": "Video",
    "webm": "Video",
    "m4v": "Video",
    "3gp": "Video",
    "3g2": "Video",
    "mpg": "Video",
    "mpeg": "Video",
    "m1v": "Video",
    "m2v": "Video",
    "mts": "Video",
    "m2ts": "Video",
    "ts": "Video",
    "vob": "Video",
    "ogv": "Video",
    "ogg": "Video",
    "dv": "Video",
    "asf": "Video",
    "rm": "Video",
    "rmvb": "Video",
    "qt": "Video",
    
    # Videos - Professional and specialized formats
    "mxf": "Video",  # Material Exchange Format
    "r3d": "Video",  # RED Cinema
    "braw": "Video", # Blackmagic RAW
    "prores": "Video", # Apple ProRes
    "dnxhd": "Video",  # Avid DNxHD
    "dnxhr": "Video",  # Avid DNxHR
    "xavc": "Video",   # Sony XAVC
    "f4v": "Video",    # Flash Video
    "dat": "Video",    # Video CD
    "divx": "Video",   # DivX
    "xvid": "Video",   # Xvid
    "y4m": "Video",    # YUV4MPEG2
    "yuv": "Video",    # Raw YUV
    
    # Audio formats
    "mp3": "Audio",
    "wav": "Audio",
    "flac": "Audio",
    "aac": "Audio",
    "ogg": "Audio",
    "wma": "Audio",
    "m4a": "Audio",
    "aiff": "Audio",
    "au": "Audio",
    "ra": "Audio",
    "3ga": "Audio",
    "amr": "Audio",
    "awb": "Audio",
    "dss": "Audio",
    "dvf": "Audio",
    "gsm": "Audio",
    "iklax": "Audio",
    "ivs": "Audio",
    "m4p": "Audio",
    "mmf": "Audio",
    "mpc": "Audio",
    "msv": "Audio",
    "opus": "Audio",
    "tta": "Audio",
    "vox": "Audio",
    "wv": "Audio"
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
