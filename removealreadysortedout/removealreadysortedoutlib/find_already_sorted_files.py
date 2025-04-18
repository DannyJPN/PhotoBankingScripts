import os
import logging
from collections import defaultdict
from tqdm import tqdm
from .get_file_paths import get_file_paths  # Use the function from get_file_paths.py

def find_already_sorted_files(unsorted_folder, target_folder):
    logging.info(f"Finding already sorted files between {unsorted_folder} and {target_folder}")

    # Get file paths from both directories
    unsorted_files = get_file_paths(unsorted_folder)
    target_files = get_file_paths(target_folder)

    # Create a dictionary to store matching files
    sorted_files_dict = defaultdict(list)

    # Create a set of target filenames (case-insensitive)
    target_filenames = {os.path.basename(f).lower(): f for f in target_files}

    # Iterate over unsorted files and find matches in target folder
    with tqdm(total=len(unsorted_files), desc="Finding sorted files", unit="file") as pbar:
        for unsorted_file in unsorted_files:
            unsorted_filename = os.path.basename(unsorted_file).lower()
            if unsorted_filename in target_filenames:
                sorted_files_dict[unsorted_file].append(target_filenames[unsorted_filename])
                logging.debug(f"DEBUGGING Files {unsorted_file} and {target_filenames[unsorted_filename]} are compared")
            pbar.update(1)

    logging.debug(f"Already sorted files: {sorted_files_dict}")
    return sorted_files_dict
