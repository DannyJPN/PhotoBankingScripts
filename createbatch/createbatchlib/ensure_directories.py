import os
import logging
import sys
from tqdm import tqdm

def ensure_directories(processed_media_folder, log_dir):
    try:
        directories = [processed_media_folder, log_dir]
        with tqdm(total=len(directories), desc="Ensuring directories", unit="dir") as pbar:
            for dir_path in directories:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                    logging.info(f"Created directory: {dir_path}")
                pbar.update(1)
    except Exception as e:
        logging.error(f"Error ensuring directories: {e}", exc_info=True)
        sys.exit(1)