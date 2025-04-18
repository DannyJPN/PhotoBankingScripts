import os
import shutil
import logging
from tqdm import tqdm
from .md5 import calculate_md5
from .display_files_gui import display_files_side_by_side_gui

def remove_sorted_files(sorted_files_dict):
    logging.info("Removing sorted files")

    with tqdm(total=len(sorted_files_dict), desc="Removing sorted files", unit="file") as pbar:
        for unsorted_file, target_files in sorted_files_dict.items():
            logging.debug(f"DEBUGGING Files {unsorted_file} and {target_files} are compared")
            if not target_files:
                pbar.update(1)
                continue

            for target_file in target_files:
                if os.path.getsize(target_file) == 0:
                    try:
                        shutil.copy2(unsorted_file, target_file)
                        logging.debug(f"Copied {unsorted_file} to {target_file}")
                    except Exception as e:
                        logging.error(f"Error copying {unsorted_file} to {target_file}: {e}")
                elif os.path.getsize(unsorted_file) != os.path.getsize(target_file) and os.path.getsize(unsorted_file) != 0:
                    logging.info(f"Files {unsorted_file} and {target_file} have different size")
                    user_input = display_files_side_by_side_gui(unsorted_file, target_file)
                    if user_input == 'y':
                        try:
                            shutil.copy2(unsorted_file, target_file)
                            logging.debug(f"Copied {unsorted_file} to {target_file}")
                        except Exception as e:
                            logging.error(f"Error copying {unsorted_file} to {target_file}: {e}")
            try:
                os.remove(unsorted_file)
                logging.debug(f"Removed unsorted file: {unsorted_file}")
            except Exception as e:
                logging.error(f"Error removing unsorted file {unsorted_file}: {e}")

            pbar.update(1)  # Update outer progress bar after each unsorted file is processed
