import os
import logging
import shutil
from typing import Dict, List
from shared.hash_utils import compute_file_hash

def get_target_files_map(target_folder: str) -> dict[str, list[str]]:
    """
    Vrátí slovník: název souboru → seznam cest, kde je nalezen v cílové složce.
    """
    logging.debug(f"Building target files map from folder: {target_folder}")
    result = {}
    
    for root, _, files in os.walk(target_folder):
        for filename in files:
            if filename not in result:
                result[filename] = []
            result[filename].append(os.path.join(root, filename))
    
    logging.debug(f"Found {sum(len(paths) for paths in result.values())} files in target folder")
    return result

def find_duplicates(unsorted_files: list[str], target_files_map: dict[str, list[str]]) -> dict[str, list[str]]:
    """
    Vrátí pouze ty soubory, jejichž jméno se shoduje s něčím v cílové složce.
    """
    duplicates = {}
    
    for file_path in unsorted_files:
        filename = os.path.basename(file_path)
        if filename in target_files_map:
            duplicates[file_path] = target_files_map[filename]
    
    logging.debug(f"Found {len(duplicates)} potential duplicates")
    return duplicates

def should_replace_file(source_path: str, target_path: str) -> bool:
    """
    Vrací True, pokud cílový soubor má nulovou velikost, nebo má jiný MD5 hash než zdrojový.
    """
    source_size = os.path.getsize(source_path)
    target_size = os.path.getsize(target_path)
    
    if target_size == 0:
        logging.debug(f"Target file has zero size: {target_path}")
        return True
    
    if source_size == 0:
        logging.debug(f"Source file has zero size: {source_path}")
        return False  # Don't replace with empty source
    
    # Compare MD5 hashes instead of just size
    try:
        source_hash = compute_file_hash(source_path)
        target_hash = compute_file_hash(target_path)
        
        if source_hash != target_hash:
            logging.debug(f"Hash mismatch: {source_path} ({source_hash}) vs {target_path} ({target_hash})")
            return True
            
        logging.debug(f"Files are identical by hash: {source_path} and {target_path}")
        return False
    except Exception as e:
        logging.error(f"Failed to compute hashes for {source_path} vs {target_path}: {e}")
        # Fallback to size comparison if hash fails
        if source_size != target_size:
            logging.debug(f"Size mismatch (hash failed): {source_path} ({source_size} bytes) vs {target_path} ({target_size} bytes)")
            return True
        return False

def handle_duplicate(source_path: str, target_paths: list[str], overwrite: bool, log_file: str) -> None:
    """
    Projde všechny kolidující soubory a rozhodne o přepisu nebo odstranění.
    """
    for target_path in target_paths:
        if not os.path.exists(target_path):
            logging.debug(f"Target file no longer exists: {target_path}")
            continue
            
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
            # Files have the same size, remove source file
            remove_if_identical(source_path, target_path, log_file)
            # Once we've handled one target file, we can stop
            break

def remove_if_identical(source_path: str, target_path: str, log_file: str) -> None:
    """
    Pokud má cílový a zdrojový soubor stejnou velikost, odstraní zdrojový a zaloguje.
    """
    try:
        os.remove(source_path)
        logging.debug(f"Removed duplicate file: {source_path} (identical to {target_path})")
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
