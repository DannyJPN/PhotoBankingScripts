import logging
import os
import shutil

from shared.file_operations import list_files
from shared.hash_utils import compute_file_hash
from tqdm import tqdm


def get_target_files_map(target_folder: str) -> dict[str, list[str]]:
    """
    Vrátí slovník: název souboru → seznam cest, kde je nalezen v cílové složce.
    """
    logging.debug(f"Building target files map from folder: {target_folder}")
    result = {}

    # First, get all files to count them for the progress bar
    all_files = list_files(target_folder, recursive=True)
    logging.debug(f"Found {len(all_files)} total files in target folder")

    # Process files with progress bar
    for file_path in tqdm(all_files, desc="Building target files map", unit="file"):
        filename = os.path.basename(file_path)
        if filename not in result:
            result[filename] = []
        result[filename].append(file_path)

    logging.debug(f"Found {sum(len(paths) for paths in result.values())} files in target folder")
    return result


def find_duplicates(unsorted_files: list[str], target_files_map: dict[str, list[str]]) -> dict[str, list[str]]:
    """
    Vrátí pouze ty soubory, jejichž jméno se shoduje s něčím v cílové složce.
    """
    duplicates = {}

    # Use progress bar to show progress
    for file_path in tqdm(unsorted_files, desc="Finding duplicates", unit="file"):
        filename = os.path.basename(file_path)
        if filename in target_files_map:
            duplicates[file_path] = target_files_map[filename]

    logging.debug(f"Found {len(duplicates)} potential duplicates")
    return duplicates


def should_replace_file(source_path: str, target_path: str) -> bool:
    """
    Vrací True, pokud cílový soubor má nulovou velikost, nebo má jinou velikost než zdrojový.
    """
    source_size = os.path.getsize(source_path)
    target_size = os.path.getsize(target_path)

    if target_size == 0:
        logging.debug(f"Target file has zero size: {target_path}")
        return True

    if source_size != target_size:
        logging.debug(f"Size mismatch: {source_path} ({source_size} bytes) vs {target_path} ({target_size} bytes)")
        return True

    return False


def get_file_hash_comparison(source_path: str, target_path: str) -> tuple[str, str, bool]:
    """
    Porovná hashe dvou souborů a vrátí je spolu s informací, zda jsou identické.

    Returns:
        Tuple obsahující (source_hash, target_hash, are_identical)
    """
    source_hash = compute_file_hash(source_path)
    target_hash = compute_file_hash(target_path)
    are_identical = source_hash == target_hash

    logging.debug(
        f"Hash comparison: {source_path} ({source_hash}) vs {target_path} ({target_hash}): {'identical' if are_identical else 'different'}"
    )

    return source_hash, target_hash, are_identical


def handle_duplicate(
    source_path: str, target_paths: list[str], overwrite: bool, log_file: str, gui_handler=None
) -> None:
    """
    Projde všechny kolidující soubory a rozhodne o přepisu nebo odstranění.
    Použije gui_handler pro rozhodnutí v případě rozdílných hashů.
    """
    try:
        # Check if source file exists
        if not os.path.exists(source_path):
            logging.debug(f"Source file no longer exists: {source_path}")
            return

        for target_path in target_paths:
            if not os.path.exists(target_path):
                logging.debug(f"Target file no longer exists: {target_path}")
                continue

            try:
                if should_replace_file(source_path, target_path):
                    if overwrite:
                        try:
                            shutil.copy2(source_path, target_path)
                            logging.info(f"Replaced target file: {target_path}")
                        except Exception as e:
                            logging.error(f"Failed to replace file {target_path}: {e}")
                    else:
                        logging.info(f"Skipping replacement of {target_path} (overwrite disabled)")
                else:
                    # Files have the same size, check hashes
                    try:
                        source_hash, target_hash, are_identical = get_file_hash_comparison(source_path, target_path)

                        if are_identical:
                            # Files are identical, remove source file
                            remove_if_identical(source_path, target_path, log_file)
                            # Once we've handled one target file, we can stop
                            break
                        else:
                            # Files have same size but different content
                            # Always use GUI to let user decide when files have same name but different content
                            if gui_handler:
                                try:
                                    # Use GUI to let user decide
                                    decision = gui_handler(source_path, target_path)
                                    if decision == "source":
                                        # Keep source, replace target
                                        try:
                                            shutil.copy2(source_path, target_path)
                                            logging.info(f"User chose to replace target with source: {target_path}")
                                        except Exception as e:
                                            logging.error(f"Failed to replace target with source {target_path}: {e}")
                                    elif decision == "target":
                                        # Keep target, remove source
                                        try:
                                            os.remove(source_path)
                                            logging.info(f"User chose to keep target and remove source: {source_path}")
                                        except Exception as e:
                                            logging.error(f"Failed to remove source {source_path}: {e}")
                                    elif decision == "both":
                                        # Keep both, do nothing
                                        logging.info(f"User chose to keep both files: {source_path} and {target_path}")
                                    elif decision == "skip":
                                        # Skip this comparison
                                        logging.info(
                                            f"User chose to skip comparison between {source_path} and {target_path}"
                                        )
                                    # Once we've handled one target file with user input, we can stop
                                    break
                                except Exception as gui_e:
                                    logging.error(f"Error in GUI handler: {gui_e}")
                                    logging.info(
                                        f"Skipping comparison due to GUI error: {source_path} and {target_path}"
                                    )
                                    break
                            else:
                                # Fallback if GUI handler is not provided (should not happen in normal operation)
                                logging.warning(
                                    f"GUI handler not provided for files with different content: {source_path} and {target_path}"
                                )
                                if overwrite:
                                    # Overwrite is enabled, replace target
                                    try:
                                        shutil.copy2(source_path, target_path)
                                        logging.info(f"Replaced target file with different hash: {target_path}")
                                    except Exception as e:
                                        logging.error(f"Failed to replace file with different hash {target_path}: {e}")
                                else:
                                    # Overwrite is disabled, skip
                                    logging.info(
                                        f"Skipping replacement of file with different hash: {target_path} (overwrite disabled)"
                                    )
                                break
                    except Exception as hash_e:
                        logging.error(f"Error comparing file hashes: {hash_e}")
                        logging.info(f"Skipping comparison due to hash error: {source_path} and {target_path}")
                        continue
            except Exception as file_e:
                logging.error(f"Error processing file pair: {source_path} and {target_path}: {file_e}")
                continue
    except Exception as e:
        logging.error(f"Error in handle_duplicate: {e}")


def remove_if_identical(source_path: str, target_path: str, log_file: str) -> None:
    """
    Pokud má cílový a zdrojový soubor stejnou velikost, odstraní zdrojový a zaloguje.
    """
    try:
        os.remove(source_path)
        logging.info(f"Removed duplicate file: {source_path} (identical to {target_path})")
    except Exception as e:
        logging.error(f"Failed to remove file {source_path}: {e}")


def remove_desktop_ini(folder: str) -> None:
    """
    Odstraní `desktop.ini`, pokud existuje.
    """
    desktop_ini_path = os.path.join(folder, "desktop.ini")
    if os.path.exists(desktop_ini_path):
        try:
            os.remove(desktop_ini_path)
            logging.info(f"Removed desktop.ini from {folder}")
        except Exception as e:
            logging.error(f"Failed to remove desktop.ini from {folder}: {e}")
