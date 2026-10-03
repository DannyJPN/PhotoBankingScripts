import os
import logging

from shared.file_operations import get_hash_map_from_folder, delete_file
from shared.hash_utils import compute_file_hash


def get_target_hash_map(target_folder: str) -> dict[str, list[str]]:
    """
    Build a content-hash → [paths] map for every file in `target_folder`.

    Using content hashes as keys means duplicate detection is name-independent:
    a file renamed to the dated format in the target is still recognised as
    the same content as its legacy-named counterpart in the unsorted folder.
    """
    path_to_hash = get_hash_map_from_folder(target_folder, pattern="", recursive=True)
    result: dict[str, list[str]] = {}
    for path, h in path_to_hash.items():
        result.setdefault(h, []).append(path)
    logging.info("Built target hash map: %d unique hashes from %s", len(result), target_folder)
    return result


def find_duplicates(
    unsorted_files: list[str],
    target_hash_map: dict[str, list[str]],
) -> dict[str, list[str]]:
    """
    Return a mapping of source_path → [matching target paths] for every file
    in `unsorted_files` whose content hash is present in `target_hash_map`.
    """
    duplicates: dict[str, list[str]] = {}
    for file_path in unsorted_files:
        try:
            h = compute_file_hash(file_path)
        except Exception as e:
            logging.error("Skipping %s (hash failed): %s", file_path, e)
            continue
        if h in target_hash_map:
            duplicates[file_path] = target_hash_map[h]
    logging.debug("Found %d duplicates", len(duplicates))
    return duplicates


def handle_duplicate(source_path: str, target_paths: list[str]) -> None:
    """
    Remove `source_path` from the unsorted folder.

    The caller guarantees that source and target share the same content hash,
    so no additional content check is needed before deletion.
    """
    for target_path in target_paths:
        if os.path.exists(target_path):
            logging.info("Removing duplicate %s (identical to %s)", source_path, target_path)
            try:
                delete_file(source_path)
            except OSError as e:
                logging.error("Failed to remove duplicate %s: %s", source_path, e)
            return
    logging.warning("No target file exists on disk for duplicate %s — keeping source", source_path)


def remove_desktop_ini(folder: str) -> None:
    """
    Remove `desktop.ini` from the folder if it exists.
    """
    desktop_ini_path = os.path.join(folder, "desktop.ini")
    if os.path.exists(desktop_ini_path):
        try:
            delete_file(desktop_ini_path)
            logging.info("Removed desktop.ini from %s", folder)
        except Exception as e:
            logging.error("Failed to remove desktop.ini: %s", e)
