import os
import logging
from tqdm import tqdm

def get_file_paths(folder_path):
    logging.info(f"Getting file paths in folder: {folder_path}")
    file_paths = []
    total_files = 0
    for root, _, files in os.walk(folder_path):
        total_files += len(files)
        logging.debug(f"Found {len(files)} files in directory: {root}")

    logging.debug(f"Calculated total files: {total_files}")

    with tqdm(total=total_files, desc="Getting file paths", unit="file") as pbar:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
                logging.debug(f"Found file: {file_path}")
                pbar.update(1)
                logging.debug(f"Progress bar updated: {pbar.n}/{pbar.total}")
    logging.debug(f"Total files found: {len(file_paths)} in {folder_path}")
    return file_paths
