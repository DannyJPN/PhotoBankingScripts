import argparse
import logging
import os
import sys
from datetime import datetime
import colorlog
import shutil
from collections import defaultdict
from tqdm import tqdm
import hashlib
from PIL import Image

# Function to configure logging
def configure_logging(log_file, debug):
    # Define log colors
    log_colors = {
        'DEBUG': 'bold_white',
        'INFO': 'bold_green',
        'WARNING': 'bold_yellow',
        'ERROR': 'bold_red',
        'CRITICAL': 'bold_purple'
    }

    # Create a log formatter
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s",
        log_colors=log_colors
    )

    # Create a log handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Create a file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # Get the root logger
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.addHandler(file_handler)

    # Set log level
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

# Function to unify files by moving all files from subdirectories to the main directory
def unify_files(folder_path):
    logging.info(f"Unifying files in folder: {folder_path}")
    file_counter = {}
    total_files = 0

    # First pass to count the total number of files
    for root, _, files in os.walk(folder_path):
        total_files += len(files)

    logging.debug(f"Total files to unify: {total_files}")

    with tqdm(total=total_files, desc="Unifying files", unit="file") as pbar:
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                new_path = os.path.join(folder_path, name)

                # Ensure unique filenames
                if new_path in file_counter:
                    file_counter[new_path] += 1
                    base, ext = os.path.splitext(new_path)
                    new_path = f"{base}_{file_counter[new_path]}{ext}"
                else:
                    file_counter[new_path] = 0

                if file_path != new_path:
                    try:
                        shutil.move(file_path, new_path)
                        logging.debug(f"Moved file {file_path} to {new_path}")
                    except Exception as e:
                        logging.error(f"Error moving file {file_path} to {new_path}: {e}")

                pbar.update(1)  # Update progress bar after each file move

            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    os.rmdir(dir_path)
                    logging.debug(f"Removed directory {dir_path}")
                except Exception as e:
                    logging.error(f"Error removing directory {dir_path}: {e}")

# Function to list all file paths in a directory recursively with a progress bar
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

# Function to find already sorted files by comparing filenames with a progress bar
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
            pbar.update(1)
            logging.debug(f"Progress bar updated: {pbar.n}/{pbar.total}")

    logging.debug(f"Already sorted files: {sorted_files_dict}")
    return sorted_files_dict

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
    except Exception as e:
        logging.error(f"Error calculating MD5 for {file_path}: {e}")
        return ""  # Return an empty string or some default value to avoid unhandled cases.
    return hash_md5.hexdigest()

def display_files_side_by_side(file1, file2):
    try:
        img1 = Image.open(file1)
        img2 = Image.open(file2)
        img1.show(title="Unsorted File")
        img2.show(title="Target File")
    except Exception as e:
        logging.error(f"Error displaying files {file1} and {file2}: {e}")

def remove_sorted_files(sorted_files_dict):
    logging.info("Removing sorted files")

    for unsorted_file, target_files in sorted_files_dict.items():
        logging.info(f"DEBUGGING Files {unsorted_file} and {target_files} are compared")
        if not target_files:
            continue

        for target_file in target_files:
            if os.path.getsize(target_file) == 0:
                try:
                    shutil.copy2(unsorted_file, target_file)
                    logging.info(f"Copied {unsorted_file} to {target_file}")
                    
                except Exception as e:
                    logging.error(f"Error copying {unsorted_file} to {target_file}: {e}")
                    continue

            if os.path.getsize(unsorted_file) == os.path.getsize(target_file):
                if calculate_md5(unsorted_file) == calculate_md5(target_file):
                    logging.info(f"Files {unsorted_file} and {target_file} are identical")
                    
                else:
                    logging.info(f"Files {unsorted_file} and {target_file} have the same size but different content")
                    display_files_side_by_side(unsorted_file, target_file)
                    try:
                        user_input = input(f"Do you want to copy {unsorted_file} to {target_file}? (y/n): ").strip().lower()
                        if user_input == 'y':
                            try:
                                shutil.copy2(unsorted_file, target_file)
                                logging.info(f"Copied {unsorted_file} to {target_file}")
                                
                            except Exception as e:
                                logging.error(f"Error copying {unsorted_file} to {target_file}: {e}")
                    except Exception as e:
                        logging.error(f"Error during user input for {unsorted_file} and {target_file}: {e}")

        try:
            os.remove(unsorted_file)
            logging.info(f"Removed unsorted file: {unsorted_file}")
        except Exception as e:
            logging.error(f"Error removing unsorted file {unsorted_file}: {e}")

# Main function to handle input parameters and configure logging
def main():
    # Define input parameters
    parser = argparse.ArgumentParser(description="RemoveAlreadySortedOut Script")
    parser.add_argument("--unsorted-folder", type=str, default="I:/NeroztříděnoTest", help="Path to the unsorted folder")
    parser.add_argument("--target-folder", type=str, default="J:/Foto/JPG", help="Path to the target folder")
    parser.add_argument("--log-file", type=str, default=None, help="Path to the log file")
    parser.add_argument("--debug", action="store_true", help="Enable debug level logging")

    # Parse input parameters
    args = parser.parse_args()

    # Sanitize and create default log file name if not provided
    if args.log_file is None:
        script_name = os.path.basename(sys.argv[0]).replace(".py", "")
        sanitized_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = f"H:/Logs/{script_name}_Log_{sanitized_date}.log"
    else:
        log_file = args.log_file

    # Configure logging
    configure_logging(log_file, args.debug)

    # Log the start of the script
    logging.info("Starting RemoveAlreadySortedOut script")
    logging.debug(f"Unsorted folder: {args.unsorted_folder}")
    logging.debug(f"Target folder: {args.target_folder}")
    logging.debug(f"Log file: {log_file}")

    # Call unify_files function
    unify_files(args.unsorted_folder)

    # Call find_already_sorted_files function
    already_sorted = find_already_sorted_files(args.unsorted_folder, args.target_folder)
    logging.debug(f"Already sorted files: {already_sorted}")

    # Call remove_sorted_files function
    remove_sorted_files(already_sorted)

if __name__ == "__main__":
    main()