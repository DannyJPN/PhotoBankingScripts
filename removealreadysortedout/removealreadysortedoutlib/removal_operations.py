import logging
import os
from collections import Counter

from shared.file_operations import delete_file, get_hash_map_from_folder
from shared.hash_utils import compute_file_hash


def get_target_hash_map(target_folder: str, path_to_hash: dict[str, str] | None = None) -> dict[str, list[str]]:
    """
    Build a content-hash → [paths] map for every file in `target_folder`.

    Using content hashes as keys means duplicate detection is name-independent:
    a file renamed to the dated format in the target is still recognised as
    the same content as its legacy-named counterpart in the unsorted folder.

    :param target_folder: Folder with sorted files.
    :param path_to_hash: Already computed path → hash map of `target_folder`; when given,
        the folder is not hashed again.
    :return: Mapping of content hash to all target paths with that content.
    """
    if path_to_hash is None:
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

    Empty files are never reported: all of them share one hash, so a single empty
    target file would otherwise mark every empty source as a duplicate.
    """
    duplicates: dict[str, list[str]] = {}
    skipped: Counter[str] = Counter()
    for file_path in unsorted_files:
        try:
            if os.path.getsize(file_path) == 0:
                logging.warning("Skipping empty file %s", file_path)
                skipped["empty file"] += 1
                continue
            h = compute_file_hash(file_path)
        except Exception as e:
            logging.error("Skipping %s (hash failed): %s", file_path, e)
            skipped["unreadable"] += 1
            continue
        if h in target_hash_map:
            duplicates[file_path] = target_hash_map[h]
    if skipped:
        logging.warning(
            "%d unsorted files were not checked for duplicates: %s",
            sum(skipped.values()),
            ", ".join(f"{count} {reason}" for reason, count in skipped.items()),
        )
    logging.debug("Found %d duplicates", len(duplicates))
    return duplicates


def handle_duplicate(source_path: str, target_paths: list[str]) -> bool:
    """
    Remove `source_path` from the unsorted folder if a target file still has the same content.

    Both files are hashed again right before deletion, because either of them may have
    changed since the hash maps were built.

    :param source_path: File in the unsorted folder.
    :param target_paths: Target files that had the same content hash during the scan.
    :return: True if the source was deleted.
    """
    try:
        source_hash = compute_file_hash(source_path)
    except Exception as e:
        logging.error("Cannot re-hash %s, keeping source: %s", source_path, e)
        return False
    for target_path in target_paths:
        if not os.path.exists(target_path):
            continue
        try:
            target_hash = compute_file_hash(target_path)
        except Exception as e:
            logging.error("Cannot re-hash %s: %s", target_path, e)
            continue
        if target_hash != source_hash:
            logging.warning("Content of %s no longer matches %s", target_path, source_path)
            continue
        logging.info("Removing duplicate %s (identical to %s)", source_path, target_path)
        try:
            delete_file(source_path)
        except OSError as e:
            logging.error("Failed to remove duplicate %s: %s", source_path, e)
            return False
        return True
    logging.warning("No identical target file exists on disk for duplicate %s — keeping source", source_path)
    return False


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
