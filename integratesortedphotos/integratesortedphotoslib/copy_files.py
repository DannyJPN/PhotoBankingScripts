import os
import logging
from tqdm import tqdm
from shared.file_operations import copy_file

def copy_files_with_preserved_dates(src_folder: str, dest_folder: str, conflict_strategy: str = "skip") -> None:
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
                if os.path.exists(dest_file):
                    if conflict_strategy == "overwrite":
                        copy_file(src_file, dest_file, overwrite=True)
                        logging.debug(f"Overwrote {dest_file} with {src_file}")
                    elif conflict_strategy == "rename":
                        resolved_path = _resolve_conflict_path(dest_file)
                        copy_file(src_file, resolved_path, overwrite=False)
                        logging.debug(f"Copied {src_file} to {resolved_path}")
                    else:
                        logging.debug(f"Skipped {src_file} as it already exists at {dest_file}")
                else:
                    copy_file(src_file, dest_file, overwrite=True)
                    logging.debug(f"Copied {src_file} to {dest_file}")
                pbar.update(1)

    except Exception as e:
        logging.error(f"An error occurred while copying files: {e}", exc_info=True)
        raise


def _resolve_conflict_path(dest_file: str) -> str:
    """
    Resolve a conflict by appending a numeric suffix.
    """
    base, ext = os.path.splitext(dest_file)
    counter = 1
    while True:
        candidate = f"{base}_{counter:03d}{ext}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1
