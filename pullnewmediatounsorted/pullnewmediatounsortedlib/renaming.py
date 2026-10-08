from shared.file_operations import delete_file, list_files, move_file
import logging
import os
import re
from collections import Counter
from datetime import datetime
from shared.file_operations import get_hash_map_from_folder, compute_file_hash
from shared.name_utils import (
    extract_camera_number,
    generate_dated_filename,
    name_key,
    resolve_name_conflict,
)
from shared.exif_handler import get_best_creation_date
from shared.exif_downloader import ensure_exiftool
from tqdm import tqdm
from pullnewmediatounsortedlib.constants import DATE_FORMAT


def replace_in_filenames(folder: str, search: str, replace: str, recursive: bool = True) -> None:
    """
    Rename files in `folder` whose name contains `search` by substituting `replace`.
    If the target name already exists the source file is removed as a duplicate.
    """
    logging.info("Replacing '%s' with '%s' in filenames under: %s", search, replace, folder)
    paths = list_files(folder, pattern=search, recursive=recursive)
    if not paths:
        logging.info("No occurrences of '%s' found in %s, skipping.", search, folder)
        return
    for path in tqdm(paths, desc="Renaming files", unit="files"):
        name = os.path.basename(path)
        if search in name:
            new_name = name.replace(search, replace)
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                if os.path.exists(new_path):
                    delete_file(path)
                    logging.debug("Removed duplicate file: %s", path)
                else:
                    move_file(path, new_path, overwrite=True)
                    logging.debug("Renamed %s to %s", path, new_path)
            except Exception as e:
                logging.error("Error replacing name for %s: %s", path, e)
                raise


def normalize_indexed_filenames(
    source_folders: list[str],
    reference_folder: str,
    prefix: str = "PICT",
) -> None:
    """
    Rename legacy ``<prefix><number>`` files in all `source_folders` to the dated format
    ``<prefix><YYYYMMDD>_<cam_seq>.<ext>`` (e.g. ``NIK_20260612_8888.JPG``).

    All source folders and the reference folder share one name space, so two different
    files from two different source folders can never receive the same name.

    Rules:
    - Only legacy names are renamed. A file that already carries a dated name keeps it forever.
    - If the file's hash is found in `reference_folder`, use the reference's canonical name.
    - Otherwise derive the shoot date from EXIF (oldest available tag, same algorithm used
      for chronological sorting) and keep the original camera sequence number.
    - A name already taken by an identical file is reused; a name taken by different content
      gets a _B, _C, … suffix.

    :param source_folders: Folders whose legacy files are renamed in place.
    :param reference_folder: Folder holding already-final names; it is never modified.
    :param prefix: Camera filename prefix, e.g. ``NIK_`` or ``PICT``.
    """
    logging.info(
        "Normalizing indexed filenames in %d source folders against %s (prefix=%s)",
        len(source_folders),
        reference_folder,
        prefix,
    )

    prefix_pattern = rf"(?i)^{re.escape(prefix)}"
    all_paths = [p for folder in source_folders for p in list_files(folder, pattern=prefix_pattern, recursive=True)]
    legacy_pattern = re.compile(rf"^{re.escape(prefix)}\d{{4,6}}\.", re.IGNORECASE)
    paths = [p for p in all_paths if legacy_pattern.match(os.path.basename(p))]
    if not paths:
        logging.info("No legacy '%s' files in %s, skipping.", prefix, source_folders)
        return

    try:
        ref_hash_map = get_hash_map_from_folder(reference_folder, pattern=prefix_pattern)
    except Exception as e:
        logging.error("Failed to build reference hash map: %s", e)
        return

    hash_to_canon: dict[str, str] = {}
    for path, h in ref_hash_map.items():
        if h not in hash_to_canon:
            hash_to_canon[h] = os.path.basename(path)
    logging.debug("Reference provides %d canonical names", len(hash_to_canon))

    used_names: dict[str, str] = {name_key(os.path.basename(p)): p for p in all_paths}
    used_names.update({name_key(os.path.basename(p)): p for p in ref_hash_map})
    known_hash: dict[str, str] = dict(ref_hash_map)

    def _hash_of(path: str) -> str | None:
        if path not in known_hash:
            try:
                known_hash[path] = compute_file_hash(path)
            except Exception as e:
                logging.error("Cannot hash %s: %s", path, e)
                return None
        return known_hash[path]

    try:
        exiftool_path = ensure_exiftool()
        logging.debug("ExifTool located at: %s", exiftool_path)
    except FileNotFoundError as e:
        logging.warning("ExifTool not found, will use filesystem dates only: %s", e)
        exiftool_path = None

    def _file_date(path: str) -> datetime:
        date = get_best_creation_date(path, tool_path=exiftool_path)
        if date is None:
            try:
                date = datetime.fromtimestamp(os.path.getmtime(path))
            except Exception:
                date = datetime.fromtimestamp(0)
        return date

    logging.info("Reading EXIF dates for %d files...", len(paths))
    path_to_date: dict[str, datetime] = {p: _file_date(p) for p in paths}
    sorted_paths = sorted(paths, key=lambda p: path_to_date[p])

    skipped: Counter[str] = Counter()
    for src_path in tqdm(sorted_paths, desc="Normalizing indexed files", unit="file"):
        name = os.path.basename(src_path)
        try:
            h = compute_file_hash(src_path)
        except Exception as e:
            logging.error("Skipping %s due to hash error: %s", src_path, e)
            skipped["hash error"] += 1
            continue
        known_hash[src_path] = h

        own_key = name_key(name)
        owned = False
        if h in hash_to_canon:
            new_name = hash_to_canon[h]
            logging.debug("Hash match: using canonical name %s", new_name)
        else:
            ext = os.path.splitext(name)[1]

            cam_num = extract_camera_number(name, prefix=prefix)
            if cam_num is None:
                logging.warning("Cannot extract camera number from '%s', skipping", name)
                skipped["no camera number"] += 1
                continue

            date_str = path_to_date[src_path].strftime(DATE_FORMAT)
            try:
                base_name = generate_dated_filename(cam_num, date_str, ext, prefix=prefix)
            except ValueError as e:
                logging.error("Cannot build dated name for '%s': %s, skipping", name, e)
                skipped["camera number out of range"] += 1
                continue
            owned = used_names.get(own_key) == src_path
            if owned:
                del used_names[own_key]
            try:
                new_name = resolve_name_conflict(
                    base_name, used_names, same_content=lambda key: _hash_of(used_names[key]) == h
                )
            except ValueError:
                logging.error("No name variant available for %s, skipping", base_name)
                skipped["no free name variant"] += 1
                if owned:
                    used_names[own_key] = src_path
                continue
            used_names[name_key(new_name)] = src_path
            logging.debug("No hash match: assigned dated name %s", new_name)

        if name_key(new_name) != name_key(name):
            dst = os.path.join(os.path.dirname(src_path), new_name)
            new_key = name_key(new_name)
            try:
                move_file(src_path, dst, overwrite=False)
                if os.path.exists(src_path):
                    logging.warning("Rename skipped, destination already exists: %s -> %s", src_path, dst)
                    skipped["destination exists"] += 1
                    if used_names.get(new_key) == src_path:
                        del used_names[new_key]
                    if owned:
                        used_names[own_key] = src_path
                else:
                    logging.debug("Renamed %s -> %s", name, new_name)
                    if used_names.get(new_key) == src_path:
                        used_names[new_key] = dst
                        known_hash[dst] = known_hash[src_path]
            except Exception as e:
                logging.error("Failed to rename %s to %s: %s", src_path, new_name, e)
                skipped["rename failed"] += 1
                if used_names.get(new_key) == src_path:
                    del used_names[new_key]
                if owned:
                    used_names[own_key] = src_path

    if skipped:
        logging.warning(
            "%d legacy '%s' files were left unrenamed: %s",
            sum(skipped.values()),
            prefix,
            ", ".join(f"{count} {reason}" for reason, count in skipped.items()),
        )
    logging.info("Completed normalization for %s", source_folders)
