import os
import logging
from PIL import Image

logging.debug("Pillow library imported successfully")

def display_files_side_by_side(file1, file2):
    try:
        img1 = Image.open(file1)
        img2 = Image.open(file2)
        img1.show(title="Unsorted File")
        img2.show(title="Target File")
    except Exception as e:
        logging.error(f"Error displaying files {file1} and {file2}: {e}", exc_info=True)