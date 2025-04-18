import os
import shutil
import logging
from tqdm import tqdm

def unify_files(folder_path):
    logging.info(f"Unifying files in folder: {folder_path}")
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

                # Ensure files are not copied into themselves and remove duplicates
                if file_path != new_path:
                    if os.path.exists(new_path):
                        logging.debug(f"File {new_path} already exists. Removing {file_path}.")
                        os.remove(file_path)
                    else:
                        try:
                            shutil.move(file_path, new_path)
                            logging.debug(f"Moved file {file_path} to {new_path}")
                        except Exception as e:
                            logging.error(f"Error moving file {file_path} to {new_path}: {e}", exc_info=True)

                pbar.update(1)  # Update progress bar after each file move

            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    os.rmdir(dir_path)
                    logging.debug(f"Removed directory {dir_path}")
                except Exception as e:
                    logging.error(f"Error removing directory {dir_path}: {e}", exc_info=True)
