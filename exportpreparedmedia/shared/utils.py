import os
from datetime import datetime
import chardet
import logging
import sys
import re
from exportpreparedmedialib.constants import EDITORIAL_REGEX, VIDEO_EXTENSIONS_FILE, IMAGE_EXTENSIONS_FILE, ILLUSTRATION_EXTENSIONS_FILE

def get_script_name():
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    logging.debug(f"Script name determined as: {script_name}")
    return script_name

def get_log_filename(log_dir):
    script_name = get_script_name()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{script_name}_Log_{current_time}.log"
    log_full_path = os.path.join(log_dir, log_filename)
    logging.debug(f"Log filename generated as: {log_full_path}")
    return log_full_path

def detect_encoding(filepath):
    with open(filepath, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def is_editorial(title, description, keywords):
    try:
        editorial_regex = re.compile(EDITORIAL_REGEX)
        if editorial_regex.match(title) or editorial_regex.match(description) or 'editorial' in keywords.lower():
            logging.debug(f"Item is editorial based on title: {title}, description: {description}, keywords: {keywords}")
            return "yes"
        logging.debug(f"Item is not editorial based on title: {title}, description: {description}, keywords: {keywords}")
        return "no"
    except Exception as e:
        logging.error(f"Error determining editorial status: {e}", exc_info=True)
        return "no"

def load_extensions(filepath):
    try:
        with open(filepath, 'r') as file:
            extensions = file.read().splitlines()
        logging.debug(f"Loaded extensions from {filepath}: {extensions}")
        return extensions
    except Exception as e:
        logging.error(f"Error loading extensions from {filepath}: {e}", exc_info=True)
        return []

# Load extensions from TXT files
video_extensions = load_extensions(VIDEO_EXTENSIONS_FILE)
image_extensions = load_extensions(IMAGE_EXTENSIONS_FILE)
illustration_extensions = load_extensions(ILLUSTRATION_EXTENSIONS_FILE)

# Add logging to verify loaded extensions
logging.debug(f"Video extensions: {video_extensions}")
logging.debug(f"Image extensions: {image_extensions}")
logging.debug(f"Illustration extensions: {illustration_extensions}")