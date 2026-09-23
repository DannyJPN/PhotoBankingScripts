import os
import logging
from tqdm import tqdm
from shared.file_operations import copy_file

def copy_files_with_preserved_dates(src_folder, dest_folder):
    """
    Copies files from src_folder to dest_folder while preserving the original creation dates.
    """
    try:
        # Create the destination folder if it doesn't exist
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)

        # Collect all files to be copied
        all_files = []
        for root, _, files in os.walk(src_folder):
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(root, src_folder)
                dest_file = os.path.join(dest_folder, rel_path, file)
                all_files.append((src_file, dest_file))

        if not all_files:
            logging.info("No files to copy from %s to %s", src_folder, dest_folder)
            return

        # Copy files with progress bar
        with tqdm(total=len(all_files), desc="Copying files", unit="file") as pbar:
            for src_file, dest_file in all_files:
                if not os.path.exists(dest_file):  # Check if the file already exists
                    copy_file(src_file, dest_file, overwrite=True)
                    logging.debug(f"Copied {src_file} to {dest_file}")
                else:
                    logging.debug(f"Skipped {src_file} as it already exists at {dest_file}")
                pbar.update(1)

    except Exception as e:
        logging.error(f"An error occurred while copying files: {e}", exc_info=True)
        raise


def find_conflicts(src_folder: str, dest_folder: str) -> list[dict[str, str]]:
    """
    Find files that would conflict in the destination.
    """
    conflicts: list[dict[str, str]] = []
    for root, _, files in os.walk(src_folder):
        for file in files:
            src_file = os.path.join(root, file)
            rel_path = os.path.relpath(root, src_folder)
            dest_file = os.path.join(dest_folder, rel_path, file)
            if os.path.exists(dest_file):
                conflicts.append({"source_path": src_file, "dest_path": dest_file})
    return conflicts
