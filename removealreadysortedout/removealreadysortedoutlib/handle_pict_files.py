import os
import re
import logging
from tqdm import tqdm
from .md5 import calculate_md5
from .get_file_paths import get_file_paths

def find_pict_files(folder_path):
    pict_files = []
    pict_pattern = re.compile(r"^PICT(\d+)\..+$", re.IGNORECASE)
    for root, _, files in os.walk(folder_path):
        for name in files:
            match = pict_pattern.match(name)
            if match:
                file_path = os.path.join(root, name)
                file_number = int(match.group(1))
                pict_files.append((file_number, file_path))
    pict_files.sort()
    return pict_files

def calculate_md5_for_files(file_paths):
    md5_to_file = {}
    with tqdm(total=len(file_paths), desc="Calculating MD5", unit="file") as pbar:
        for _, fp in file_paths:
            md5 = calculate_md5(fp)
            md5_to_file[md5] = fp
            pbar.update(1)
    return md5_to_file

def prepare_renaming_pairs(pict_files, target_md5_to_file, highest_target_number, existing_filenames, unsorted_filenames):
    renaming_pairs = []
    highest_planned_number = highest_target_number
    with tqdm(total=len(pict_files), desc="Preparing renaming pairs", unit="file") as pbar:
        for file_number, file_path in pict_files:
            try:
                file_md5 = calculate_md5(file_path)
                logging.debug(f"File: {file_path}, MD5: {file_md5}")
                logging.debug(f"Comparing MD5 of {file_path} to target PICTs")
    
                if file_md5 in target_md5_to_file:
                    existing_file_path = target_md5_to_file[file_md5]
                    existing_file_name = os.path.basename(existing_file_path)
                    if os.path.basename(file_path) != existing_file_name:
                        new_file_name = existing_file_name
                        new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)
                        renaming_pairs.append((file_path, new_file_path))
                        logging.debug(f"Planned renaming {file_path} to {new_file_path} (Matched with existing file: {existing_file_path})")
                    else:
                        logging.debug(f"No renaming needed for {file_path} (MD5 match with {existing_file_path})")
                    highest_planned_number = max(highest_planned_number, int(re.search(r'\d+', existing_file_name).group()))
                else:
                    if renaming_pairs:
                        highest_planned_number = max(highest_planned_number, max(int(re.search(r'\d+', os.path.basename(new_path)).group()) for _, new_path in renaming_pairs))
                    else:
                        highest_planned_number = highest_target_number
    
                    logging.debug(f"Highest planned number for renaming: {highest_planned_number}")
    
                    new_file_number = highest_planned_number + 1
                    while True:
                        new_file_name = f"PICT{new_file_number:04d}{os.path.splitext(file_path)[1]}"
                        new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)
                        logging.debug(f"Trying {new_file_name} for {file_path}")
                        if new_file_name not in existing_filenames and new_file_name not in unsorted_filenames and new_file_name not in {os.path.basename(new_path) for _, new_path in renaming_pairs}:
                            logging.debug(f"SUCCESS {new_file_name} for {file_path}")
                            break
                        new_file_number += 1
    
                    renaming_pairs.append((file_path, new_file_path))
                    logging.debug(f"Planned renaming {file_path} to {new_file_path} (New sequence number)")
    
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}", exc_info=True)
            pbar.update(1)
    return renaming_pairs

def rename_files(renaming_pairs):
    for old_path, new_path in renaming_pairs:
        logging.debug(f"Renaming {old_path} to {new_path}")
        try:
            if os.path.basename(old_path) != os.path.basename(new_path):
                os.rename(old_path, new_path)
                logging.debug(f"Renamed {old_path} to {new_path}")
            else:
                logging.debug(f"Renaming skipped: {old_path} to {new_path}")
        except Exception as e:
            logging.error(f"Error renaming file {old_path} to {new_path}: {e}", exc_info=True)

def handle_pict_files(unsorted_folder, target_folder):
    logging.info(f"Handling PICT files in folder: {unsorted_folder}")

    pict_files = find_pict_files(unsorted_folder)
    logging.info(f"Found {len(pict_files)} PICT files")

    target_pict_files = [(int(re.match(r"^PICT(\d+)\..+$", os.path.basename(fp)).group(1)), fp)
                         for fp in get_file_paths(target_folder) if re.match(r"^PICT(\d+)\..+$", os.path.basename(fp))]
    target_pict_files.sort()

    target_md5_to_file = calculate_md5_for_files(target_pict_files)

    highest_target_number = max((num for num, _ in target_pict_files), default=0)
    logging.info(f"Highest number in target PICT files: {highest_target_number}")

    existing_filenames = {os.path.basename(fp) for _, fp in target_pict_files}
    logging.info(f"Existing filenames in target folder: {len(existing_filenames)}")

    unsorted_filenames = {os.path.basename(fp) for _, fp in pict_files}
    logging.info(f"Existing filenames in unsorted folder: {len(unsorted_filenames)}")

    if len(pict_files) == 0:
        return

    renaming_pairs = prepare_renaming_pairs(pict_files, target_md5_to_file, highest_target_number, existing_filenames, unsorted_filenames)
    renaming_pairs.sort(key=lambda pair: int(re.search(r'\d+', os.path.basename(pair[1])).group()), reverse=True)

    rename_files(renaming_pairs)

    logging.info(f"Renamed {len(renaming_pairs)} PICT files based on MD5 hashes and numeric order.")
