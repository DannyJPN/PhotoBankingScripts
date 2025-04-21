"""
Regular expression patterns for the UpdateMediaDatabase project.
Contains patterns for recognizing edited files, camera models, etc.
"""
import re

# Regex patterns for edit types in filenames
EDIT_PATTERNS = {
    'bw': r'_bw\b|_blackwhite\b|_blackandwhite\b|_black[\s_-]?white\b|_monochrome\b',
    'sepia': r'_sepia\b',
    'vintage': r'_vintage\b|_retro\b',
    'blur': r'_blur(?:red)?\b',
    'sharpen': r'_sharp(?:en(?:ed)?)?\b',
    'hdr': r'_hdr\b',
    'panorama': r'_pano(?:rama)?\b',
    'crop': r'_crop(?:ped)?\b',
    'square': r'_square\b|_sq\b',
    'portrait': r'_portrait\b|_port\b',
    'landscape': r'_landscape\b|_land\b',
    'negative': r'_negative\b|_neg\b',
    'vignette': r'_vignette\b|_vign\b',
    'tilt': r'_tilt(?:shift)?\b',
    'composite': r'_composite\b|_comp\b',
    'collage': r'_collage\b',
    'frame': r'_frame(?:d)?\b',
    'watermark': r'_watermark(?:ed)?\b|_wm\b',
    'text': r'_text\b',
    'filter': r'_filter\b',
    'effect': r'_effect\b',
    'art': r'_art\b',
    'sketch': r'_sketch\b',
    'cartoon': r'_cartoon\b',
    'oil': r'_oil(?:paint(?:ing)?)?\b',
    'pencil': r'_pencil\b',
    'drawing': r'_drawing\b',
    'painting': r'_painting\b',
    'abstract': r'_abstract\b',
    'grunge': r'_grunge\b',
    'aged': r'_aged\b',
    'color': r'_color(?:ized)?\b',
    'enhanced': r'_enhanced\b|_enhance\b',
    'edited': r'_edit(?:ed)?\b',
}

# Compiled regex patterns for better performance
COMPILED_EDIT_PATTERNS = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in EDIT_PATTERNS.items()}

# Combined pattern for any edit
ANY_EDIT_PATTERN = re.compile('|'.join(EDIT_PATTERNS.values()), re.IGNORECASE)

# Pattern to extract original filename from edited filename
# Example: "IMG_1234_bw.jpg" -> "IMG_1234.jpg"
ORIGINAL_FILENAME_PATTERN = re.compile(r'^(.+?)(?:_(?:bw|blackwhite|blackandwhite|sepia|vintage|retro|blur|blurred|sharp|sharpen|sharpened|hdr|pano|panorama|crop|cropped|square|sq|portrait|port|landscape|land|negative|neg|vignette|vign|tilt|tiltshift|composite|comp|collage|frame|framed|watermark|watermarked|wm|text|filter|effect|art|sketch|cartoon|oil|oilpaint|oilpainting|pencil|drawing|painting|abstract|grunge|aged|color|colorized|enhanced|enhance|edit|edited))+(\.[^.]+)$', re.IGNORECASE)

# Camera and lens model patterns
CAMERA_PATTERNS = {
    'nikon': r'nikon\s+\w+\d+',
    'canon': r'canon\s+eos\s+\w+',
    'sony': r'sony\s+a\d+',
    'fuji': r'fuji(?:film)?\s+x-\w+',
    'olympus': r'olympus\s+\w+-\d+',
    'panasonic': r'panasonic\s+lumix\s+\w+\d+',
    'leica': r'leica\s+\w+',
    'pentax': r'pentax\s+\w+\d+',
    'hasselblad': r'hasselblad\s+\w+',
    'gopro': r'gopro\s+hero\d+',
    'dji': r'dji\s+\w+\s+\d+',
    'iphone': r'iphone\s+\d+(?:\s+pro)?',
    'samsung': r'samsung\s+galaxy\s+\w+\d+',
    'google': r'google\s+pixel\s+\d+',
}

# Compiled camera patterns
COMPILED_CAMERA_PATTERNS = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in CAMERA_PATTERNS.items()}
